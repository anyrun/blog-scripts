using System;
using System.Collections.Generic;
using System.Linq;
using dnlib.DotNet;
using dnlib.DotNet.Emit;

namespace Example11
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

                    // obfuscate control flow
                    ProtectCFG(newMethod);

                    // obfuscate int values
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
                
                var obfExpr = Expressions.GenObfExpr(target, temp);

                // can't simple remove the old instruction, cuz it might be
                // targeted by the conditional expression
                instr[i].Operand = obfExpr[0].Operand;
                obfExpr.RemoveAt(0);

                var next_i = i;
                obfExpr.ForEach(expr => instr.Insert(++next_i, expr));
            }
        }

        private void ProtectCFG(MethodDef method)
        {
            var blocks = SplitToBlocks(method);

            ApplySwitch(method, blocks);
        }

        private List<Instruction[]> SplitToBlocks(MethodDef method)
        {
            // check if method has a non-empty return
            bool hasReturnValue = method.ReturnType.RemoveModifiers().ElementType != ElementType.Void;

            // get method body
            var body = method.Body;

            // initial stack value
            int currentStack = 0;

            var simpleBlock = new List<Instruction>();
            var blocks = new List<Instruction[]>();

            // go through all the instructions
            for (int i = 0; i < body.Instructions.Count; i++)
            {
                // current instruction
                var instr = body.Instructions[i];

                // add the next instruction to the current simple block
                simpleBlock.Add(instr);

                // update the stack as needed
                instr.UpdateStack(ref currentStack, hasReturnValue);

                // can't split here
                if (currentStack > 0) continue;

                // add the next simple block
                blocks.Add(simpleBlock.ToArray());

                // prepare the next block
                simpleBlock.Clear();
            }

            return blocks;
        }
        private void ApplySwitch(MethodDef method, List<Instruction[]> blocks)
        {
            var body = method.Body;

            // prepare the body
            var instr = body.Instructions;
            instr.Clear();

            // keep the next choice
            var num = new Local(_module.CorLibTypes.Int32);
            body.Variables.Add(num);

            // generate a random locations
            var shuffBlocksId = Enumerable.Range(0, blocks.Count).ToArray();
            Utils.Shuffle(shuffBlocksId);

            var ids = new Dictionary<int, int>();
            for (int id = 0; id < shuffBlocksId.Count(); id++)
                ids[shuffBlocksId[id]] = id;

            // add the start case
            instr.Add(OpCodes.Ldc_I4.ToInstruction(ids[0]));
            instr.Add(OpCodes.Stloc.ToInstruction(num));

            // switch statement starts from this instruction
            Instruction switch_start = OpCodes.Ldloc.ToInstruction(num);
            instr.Add(switch_start);

            // create a switch
            var switchInstr = new Instruction(OpCodes.Switch);
            var switchTargets = new List<Instruction>();

            // add switch targets in random order
            for (int i = 0; i < shuffBlocksId.Length; i++)
            {
                switchTargets.Add(blocks[shuffBlocksId[i]][0]);
            }
            switchInstr.Operand = switchTargets;
            instr.Add(switchInstr);

            // create infinite loop now, but add it later 
            Instruction brInfiniteLoop = OpCodes.Br.ToInstruction(switch_start);

            // default case follows immediately after the switch
            instr.Add(OpCodes.Br.ToInstruction(brInfiniteLoop));

            foreach (var id in shuffBlocksId)
            {
                // add all instructions from the current simple block
                foreach (var currInstr in blocks[id])
                {
                    instr.Add(currInstr);
                }

                int next_num;
                if (ids.TryGetValue(id + 1, out next_num))
                {
                    instr.Add(OpCodes.Ldc_I4.ToInstruction(next_num));
                    instr.Add(OpCodes.Stloc.ToInstruction(num));
                }

                instr.Add(OpCodes.Br.ToInstruction(brInfiniteLoop));
            }

            // loop forever
            instr.Add(brInfiniteLoop);
        }
    }
}
