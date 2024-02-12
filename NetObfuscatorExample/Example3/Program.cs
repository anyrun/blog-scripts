using System;

namespace Example3
{
    internal class Program
    {
        public const string src = "Example1.exe";
        public const string dst = "Example1_obf.exe";

        public const string className = "Example1.Program";
        public const string methodName = "ProtectMe";
        static void Main(string[] args)
        {
            try
            {
                // create obfuscator
                var obfuscator = new SimpleObfuscator(src, dst);

                // obfuscate function "ProtectMe"
                obfuscator.Obfuscate(className, methodName);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[ERROR] {ex.Message}");
            }            
        }
    }
}
