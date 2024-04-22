/*
    This rule is not designed to detect and identify Guloader itself. 
    Instead, its purpose is to help you find specific offsets within dumps that will be used for emulation.
*/

rule GuLoader_emulation{
    meta:
        author = "Any.Run"
        date = "2024/04/04"
        family = "guloader"
        sha256 = "3b0b1b064f6b84d3b68b541f073ddca759e01adbbb9c36e7b38e6707b941539e"
        anyrun_task = "https://app.any.run/tasks/aabc765a-ff14-4e8f-902b-75ae29809d1f"


    strings:
        
    // 89 44 24 28  MOV          dword ptr [ESP + 0x28],EAX
    // 66 85 c0     TEST         AX,AX
    // e9 61 f3     JMP          FUN_00df93f3
    $decryptor = {89 44 24 28 [0-20] e9 }

    // 8b 4c 24 04  MOV          ECX,dword ptr [ESP + 0x4]
    $cyphertext = {8b ?? 24 04}

   // 39 48 08             CMP      dword ptr   [EAX + 0x8] , ECX
   // 75 84                JNZ      LAB_00532d70
   // 39 48 0c             CMP      dword ptr   [EAX + 0xc] , ECX
   // 0f 85 7b ff ff ff    JNZ      LAB_00532d70
   // 66 85 db             TEST     BX, BX
   // 39 48 10             CMP      dword ptr   [EAX + 0x10] , ECX
   // 0f 85 6f ff ff ff    JNZ      LAB_00532d70
   // 39 48 14             CMP      dword ptr   [EAX + 0x14] , ECX
   // 0f 85 66 ff ff ff    JNZ      LAB_00532d70
   // 39 48 18             CMP      dword ptr   [EAX + 0x18] , ECX
   // 0f 85 5d ff ff ff    JNZ      LAB_00532d70
   // b9 65 2c 2c b8       MOV      ECX , 0xb82c2c65
    $veh_xor_key = { 39 48 14 (75 | 0f) [1-5] [0-10] 39 48 18 (75 | 0f) [1-5] [0-10] b9}

    // 01 d0        ADD          EAX,EDX
    // 66 85 d9     TEST         CX,BX
    // 8b 10        MOV          EDX,dword ptr [EAX]
    // 83 c2 04     ADD          EDX,0x4
    $offset_from_exception = {01 d0 [0-10] 8b 10 [0-10] 83 c2}

    condition:
        all of them
}