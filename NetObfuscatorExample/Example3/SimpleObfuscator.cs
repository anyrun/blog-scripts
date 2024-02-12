using System;
using dnlib.DotNet;
using dnlib.DotNet.Emit;

namespace Example3
{
    internal class SimpleObfuscator
    {
        private string _dst;

        private ModuleDefMD mod;

        public SimpleObfuscator(string src, string dst)
        {
            _dst = dst;

            // load assembly
            mod = ModuleDefMD.Load(src);
        }

        public void Obfuscate(string typeName, string methodName)
        {
            // get type
            var t = mod.Find(typeName, true);

            // get method
            var m = t.FindMethod(methodName);

            if (m != null)
            {
                ObfuscateInternal(t, m);

                // save the result
                mod.Write(_dst);
            }            
        }

        private void ObfuscateInternal(TypeDef t, MethodDef m)
        {
            // create a new obfuscator class
            var obf = new TypeDefUser(Utils.GetRandStr(), Utils.GetRandStr(), mod.CorLibTypes.Object.TypeDefOrRef);

            // set class attributes to make it static
            obf.Attributes = TypeAttributes.Public | TypeAttributes.Abstract | TypeAttributes.Sealed;

            // add obfuscator to the assembly
            mod.Types.Add(obf);

            ProtectStrings(obf, t, m);
        }

        private void ProtectStrings(TypeDef obf, TypeDef t, MethodDef m)
        {
            // check if the method has instructions
            if (m.HasBody)
            {
                // get instructions
                var instr = m.Body.Instructions;

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
                            MethodSig.CreateStatic(mod.CorLibTypes.String),
                            MethodImplAttributes.IL | MethodImplAttributes.Managed,
                            MethodAttributes.Public | MethodAttributes.Static
                        );

                        // create the method body
                        newMethod.Body = new CilBody();

                        // get the instructions
                        var newInstr = newMethod.Body.Instructions;

                        // add load string instruction
                        newInstr.Add(OpCodes.Ldstr.ToInstruction(s));

                        // add return instruction
                        newInstr.Add(OpCodes.Ret.ToInstruction());

                        // append the new method to the type
                        obf.Methods.Add(newMethod);

                        // replace the original istruction with the call to obfuscated function
                        instr[i] = OpCodes.Call.ToInstruction(newMethod);
                    }
                }
            }
        }
    }
}
