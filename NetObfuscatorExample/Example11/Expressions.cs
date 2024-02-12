using dnlib.DotNet.Emit;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Example11
{
    public class Expressions
    {
        public static List<Instruction> GenObfExpr(int targetValue, Local temp, int initialValue = 0, int maxIterations = 5)
        {            
            switch (Utils.random.Next(2))
            {
                case 0:
                    return GenObfAddSubExpr(targetValue, temp, initialValue, maxIterations);
                case 1:
                    return GenObfXorExpr(targetValue, temp, initialValue, maxIterations);
                default:
                    break;
            }

            return null;
        }
        public static List<Instruction> GenObfAddSubExpr(int targetValue, Local temp, int initialValue = 0, int maxIterations = 5)
        {
            List<Instruction> instructions = new List<Instruction>();

            int currentValue = initialValue;
            if (currentValue == 0)
                currentValue = Utils.random.Next();

            // trick against IlSpy - we save the initial number to the temp
            // variable to prevent synthesizing expressions
            instructions.Add(Instruction.Create(OpCodes.Ldc_I4, currentValue));
            instructions.Add(Instruction.Create(OpCodes.Stloc, temp));

            instructions.Add(Instruction.Create(OpCodes.Ldloc, temp));

            if (maxIterations < 3)
                maxIterations = 3;
            
            for (var iterations = 0; iterations < Utils.random.Next(1, maxIterations); iterations++)
            {
                // Randomly choose between add, sub
                int operation = Utils.random.Next(2);
                int operand = Utils.random.Next();

                if (operation == 0) // Add
                {
                    currentValue += operand;
                    instructions.Add(Instruction.Create(OpCodes.Ldc_I4, operand));
                    if (Utils.random.Next(2) > 0) // only to increase chaos :-)
                        instructions.Add(Instruction.Create(OpCodes.Conv_U4));
                    instructions.Add(Instruction.Create(OpCodes.Add));
                }
                else // Sub
                {
                    currentValue -= operand;
                    instructions.Add(Instruction.Create(OpCodes.Ldc_I4, operand));
                    if (Utils.random.Next(2) > 0) // only to increase chaos :-)
                        instructions.Add(Instruction.Create(OpCodes.Conv_U4));
                    instructions.Add(Instruction.Create(OpCodes.Sub));
                }
            }

            // Final adjustment to match the target value
            if (currentValue != targetValue)
            {
                int finalAdjustment = targetValue - currentValue;
                if (finalAdjustment > 0)
                {
                    instructions.Add(Instruction.Create(OpCodes.Ldc_I4, finalAdjustment));
                    instructions.Add(Instruction.Create(OpCodes.Add));
                }
                else
                {
                    instructions.Add(Instruction.Create(OpCodes.Ldc_I4, -finalAdjustment));
                    instructions.Add(Instruction.Create(OpCodes.Sub));
                }
            }

            return instructions;
        }

        public static List<Instruction> GenObfXorExpr(int targetValue, Local temp, int initialValue = 0, int maxIterations = 5)
        {
            List<Instruction> instructions = new List<Instruction>();

            int currentValue = initialValue;
            if (currentValue == 0)
                currentValue = Utils.random.Next();

            // trick against IlSpy - we save the initial number to the temp
            // variable to prevent synthesizing expressions
            instructions.Add(Instruction.Create(OpCodes.Ldc_I4, currentValue));
            instructions.Add(Instruction.Create(OpCodes.Stloc, temp));

            instructions.Add(Instruction.Create(OpCodes.Ldloc, temp));

            if (maxIterations < 3)
                maxIterations = 3;

            for (var iterations = 0; iterations < Utils.random.Next(1, maxIterations); iterations++)
            {
                int operand = Utils.random.Next(); // Generate random byte
                currentValue ^= operand;
                instructions.Add(OpCodes.Ldc_I4.ToInstruction(operand));
                if (Utils.random.Next(2) > 0) // only to increase chaos :-)
                    instructions.Add(Instruction.Create(OpCodes.Conv_U4));
                instructions.Add(OpCodes.Xor.ToInstruction());

                iterations++;
            }

            // Final adjustment to match the target value
            int finalAdjustment = targetValue ^ currentValue;
            instructions.Add(OpCodes.Ldc_I4.ToInstruction(finalAdjustment));
            instructions.Add(OpCodes.Xor.ToInstruction());

            return instructions;
        }
    }
}
