using System;

namespace Example1
{
    internal class Program
    {
        static void Main(string[] args)
        {
            ProtectMe();
        }

        static void ProtectMe()
        {
            //string secretCode = "No_On3_Can_Find_My_S3cr37_Pass";
            string secretCode = "ONE";
            Console.WriteLine(secretCode);
        }
    }
}
