using System;
using System.Collections.Generic;
using System.Linq;
using dnlib.DotNet;
using dnlib.DotNet.Emit;

namespace Example9
{
    internal class SimpleObfuscator
    {
        private string _dst;

        private TypeDef _type;
        private ModuleDefMD _module;
        private TypeDefUser _obfuscator;

        public SimpleObfuscator(string src, string dst)
        {
            _dst = dst;

            // load assembly
            _module = ModuleDefMD.Load(src);
        }

        public void Obfuscate(string typeName, string methodName)
        {
            // get type
            _type = _module.Find(typeName, true);

            // get method
            var method = _type.FindMethod(methodName);

            if (method != null && method.HasBody)
            {
                ObfuscateInternal(method);

                // save the result
                _module.Write(_dst);
            }
        }

        private void ObfuscateInternal(MethodDef method)
        {
            // create a new obfuscator class
            _obfuscator = new TypeDefUser(Utils.GetRandStr(), Utils.GetRandStr(), _module.CorLibTypes.Object.TypeDefOrRef);

            // set class attributes to make it static
            _obfuscator.Attributes = TypeAttributes.Public | TypeAttributes.Abstract | TypeAttributes.Sealed;

            // add obfuscator to the assembly
            _module.Types.Add(_obfuscator);

            ProtectStrings(method);
        }

        private void ProtectStrings(MethodDef method)
        {
            // get instructions
            var instr = method.Body.Instructions;

            // go through all the instructions
            for (int i = 0; i < instr.Count; i++)
            {
                // find each instance of "ldstr" (load string)
                if (instr[i].OpCode == OpCodes.Ldstr)
                {
                    // check if we found a non-empty string
                    var s = (string)instr[i].Operand;
                    if (s.Length == 0)
                        continue;

                    // create a new static method with random name
                    MethodDef newMethod = new MethodDefUser(
                        Utils.GetRandStr(),
                        MethodSig.CreateStatic(_module.CorLibTypes.String),
                        MethodImplAttributes.IL | MethodImplAttributes.Managed,
                        MethodAttributes.Public | MethodAttributes.Static
                    );

                    // create the method body                        
                    var body = new CilBody();
                    body.InitLocals = true;

                    // split string by bytes
                    var splStr = SplitStringByCharToInstr(body, s);

                    // get the instructions
                    var newInstr = body.Instructions;
                    splStr.ForEach(sInstr => newInstr.Add(sInstr));

                    // set method body
                    newMethod.Body = body;

                    // hide characters with their numeric values
                    MaskCharsWithNumVal(newMethod);

                    ProtectNumWithExpr(newMethod);

                    // append the new method to the type
                    _obfuscator.Methods.Add(newMethod);

                    // replace the original istruction with the call to obfuscated function
                    instr[i] = OpCodes.Call.ToInstruction(newMethod);
                }
            }
        }

        private List<Instruction> SplitStringByCharToInstr(CilBody body, string s)
        {
            // create a new variable where we keep the result string
            var res = new Local(_module.CorLibTypes.String);
            body.Variables.Add(res);
            
            var instr = new List<Instruction>();

            // save the first char into the variable
            instr.Add(OpCodes.Ldstr.ToInstruction(s[0].ToString()));
            instr.Add(OpCodes.Stloc.ToInstruction(res));

            for (int i = 1; i < s.Length; i++)
            {
                // concatenate the next char and the variable
                instr.Add(OpCodes.Ldloc.ToInstruction(res));
                instr.Add(OpCodes.Ldstr.ToInstruction(s[i].ToString()));

                var concatMethod = _module.Import(typeof(string).GetMethod("Concat", new[] { typeof(string), typeof(string) }));
                instr.Add(OpCodes.Call.ToInstruction(concatMethod));

                instr.Add(OpCodes.Stloc.ToInstruction(res));
            }

            // return result
            instr.Add(OpCodes.Ldloc.ToInstruction(res));
            instr.Add(OpCodes.Ret.ToInstruction());

            return instr;
        }

        private void MaskCharsWithNumVal(MethodDef method)
        {
            var body = method.Body;

            var ch = new Local(_module.CorLibTypes.Char);
            body.Variables.Add(ch);

            var instr = body.Instructions;

            for (int i = instr.Count - 1; i >= 0; i--)
            {
                if (instr[i].OpCode != OpCodes.Ldstr)
                    continue;

                var s = (string)instr[i].Operand;
                if (s.Length != 1)
                    continue;

                instr.RemoveAt(i);

                int next_i = i;

                // magic is here: int32 -> unsigned int16 to hide char
                instr.Insert(next_i++, OpCodes.Ldc_I4.ToInstruction((int)s[0]));
                instr.Insert(next_i++, OpCodes.Conv_U2.ToInstruction());
                instr.Insert(next_i++, OpCodes.Stloc.ToInstruction(ch));

                instr.Insert(next_i++, OpCodes.Ldloca.ToInstruction(ch));
                var toStringMemberRef = _module.Import(typeof(char).GetMethod("ToString", new Type[] { }));
                instr.Insert(next_i++, OpCodes.Call.ToInstruction(toStringMemberRef));
            }
        }

        private void ProtectNumWithExpr(MethodDef method)
        {
            var body = method.Body;

            var temp = new Local(_module.CorLibTypes.Int32);
            body.Variables.Add(temp);

            var instr = body.Instructions;

            for (int i = instr.Count - 1; i >= 0; i--)
            {
                if (instr[i].OpCode != OpCodes.Ldc_I4)
                    continue;

                // target number we need to obfuscate
                var target = (int)instr[i].Operand;

                // remove the original one
                instr.RemoveAt(i);
                
                var obfExpr = Expressions.GenObfExpr(target, temp);

                var next_i = i;
                obfExpr.ForEach(expr => instr.Insert(next_i++, expr));
            }
        }
    }
}
