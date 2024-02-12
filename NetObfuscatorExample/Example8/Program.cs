using System;

namespace Example8
{
    internal class Program
    {   
        static void Main(string[] args)
        {
            int ch;
            string secretCode = "";

            // 'A' character using add/sub
            ch = 0x12345678;
            ch = (int)(ch - 0x87654321);
            ch += 0x7530ECEA;
            secretCode += ((char)ch).ToString();

            // 'A' character using xor
            ch = 0x12345678;
            ch = (int)(ch ^ 0x87654321);
            ch = (int)(ch ^ 0x95511518);
            secretCode += ((char)ch).ToString();

            // 'AA'
            Console.WriteLine(secretCode);
        }
    }
}
