using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Example3
{
    internal class Utils
    {
        private static readonly Random random = new Random();
        //private static readonly string allowedChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_";

        private const int HieroglyphStart = 0x13000;
        private const int HieroglyphEnd = 0x14000;

        public static string GetRandStr(int min = 7, int max = 15)
        {
            
            var l = random.Next(min, max + 1);
            var s = new StringBuilder(l);
            for (int i = 0; i < l; i++)
            {
                //s.Append(allowedChars[random.Next(allowedChars.Length)]);

                var charCode = random.Next(HieroglyphStart, HieroglyphEnd + 1);
                var hieroglyph = char.ConvertFromUtf32(charCode);
                s.Append(hieroglyph);
            }
            return s.ToString();
        }        
    }
}
