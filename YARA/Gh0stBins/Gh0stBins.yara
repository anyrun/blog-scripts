rule Gh0stBINS_Shfolder
{
    meta:
        Author = "Any.Run"
        Date = "2023-06-01"

    strings:
        $pdb = "E:\\MyProjects\\\xE8\xBF\x87\xE5\x90\xAF\xE5\x8A\xA8\\FakeDll\\Release\\shfolder.pdb"
        $decode_routine = {83 E0 07 0F B6 44 05 F0 30 81 [4] 8D [5] 03 C1}

    condition:
        all of them
}

rule Gh0stBINS_PayloadDecrypted
{
    meta:
        Author = "Any.Run"
        Date = "2023-06-01"

    strings:
        $cmd1 = "chat"
        $cmd2 = "filemgr"
        $cmd3 = "camera"
        $cmd4 = "filedownloader"
        $cmd5 = "kblog"
        $cmd6 = "socksproxy"

        $str1 = "Not Recv Heartbeat ,Time out...."
        $str2 = "CIOCPClient::PostRead WSARecv Failed with %d"
        $str3 = "CIOCPClient::PostWrite WSASend Failed with %d"
        $str4 = "CIOCPClient::OnConnect()"
        $str5 = "Load From Mem Failed..."
        $str6 = "load module successed :%s"

        $w_str1 = "SHGetSpecialFolderPath Failed With Error : %u" wide
        $w_str2 = "CoCreateInstance Failed With Error : %u" wide
        $w_str3 = "Copy To Startup Menu Failed (%d)!" wide
        $w_str4 = "Copy To Startup Menu Success!" wide
        $w_str5 = "SOFTWARE\\HHClient" wide
        $w_str6 = "VMware NAT Service" wide

    condition:
        all of them
}

rule Gh0stBINS_DumpDD0
{
    meta:
        Author = "Any.Run"
        Date = "2023-06-01"

    strings:
        $pdb = "E:\\MyProjects\\\xE8\xBF\x87\xE5\x90\xAF\xE5\x8A\xA8\\FakeDll\\fakedll\\Loader.pdb"

        $str1 = "AntiKill::auxProcess" wide
        $str2 = "\\vmnet.exe" wide
        $str3 = "\\net-service.exe" wide
        $str4 = "VMware NAT Service" wide
        $str5 = "GET /update/ HTTP/1.1"

    condition:
        $pdb
            or
        all of ($str*)
}

rule Gh0stBINS_Dump0D0
{
    meta:
        Author = "Any.Run"
        Date = "2023-06-01"

    strings:
        $sig_func_name1 = {C6 4? ?? 47 C6 4? ?? 65 C6 4? ?? 74 C6 4? ?? 4D C6 4? ?? 6F C6 4? ?? 64 C6 4? ?? 75 C6 4? ?? 6C C6 4? ?? 65 C6 4? ?? 48 C6 4? ?? 61 C6 4? ?? 6E C6 4? ?? 64 C6 4? ?? 6C C6 4? ?? 65 C6 4? ?? 41 C6 4? ?? 00}
        $sig_func_name2 = {C6 4? ?? 4C C6 4? ?? 6F C6 4? ?? 61 C6 4? ?? 64 C6 4? ?? 4C C6 4? ?? 69 C6 4? ?? 62 C6 4? ?? 72 C6 4? ?? 61 C6 4? ?? 72 C6 4? ?? 79 C6 4? ?? 41 C6 4? ?? 00}
        $sig_func_name3 = {C6 4? ?? 6C C6 4? ?? 73 C6 4? ?? 74 C6 4? ?? 72 C6 4? ?? 63 C6 4? ?? 70 C6 4? ?? 79 C6 4? ?? 6E C6 4? ?? 41 C6 4? ?? 00}
        $sig_func_name4 = {C6 4? ?? 56 C6 4? ?? 69 C6 4? ?? 72 C6 4? ?? 74 C6 4? ?? 75 C6 4? ?? 61 C6 4? ?? 6C C6 4? ?? 41 C6 4? ?? 6C C6 4? ?? 6C C6 4? ?? 6F C6 4? ?? 63 C6 4? ?? 00}
        $sig_func_name5 = {C6 4? ?? 56 C6 4? ?? 69 C6 4? ?? 72 C6 4? ?? 74 C6 4? ?? 75 C6 4? ?? 61 C6 4? ?? 6C C6 4? ?? 50 C6 4? ?? 72 C6 4? ?? 6F C6 4? ?? 74 C6 4? ?? 65 C6 4? ?? 63 C6 4? ?? 74 C6 4? ?? 00}

        $lib = {B? 6B 00 00 00 66 89 ?? ?? ?? ?? ?? B? 65 00 00 00 66 89 ?? ?? ?? ?? ?? B? 72 00 00 00 66 89 ?? ?? ?? ?? ?? B? 6E 00 00 00 66 89 ?? ?? ?? ?? ?? B? 65 00 00 00 66 89 ?? ?? ?? ?? ?? B? 6C 00 00 00 66 89 ?? ?? ?? ?? ?? B? 33 00 00 00 66 89 ?? ?? ?? ?? ?? B? 32 00 00 00 66 89 ?? ?? ?? ?? ?? B? 2E 00 00 00 66 89 ?? ?? ?? ?? ?? B? 64 00 00 00 66 89 ?? ?? ?? ?? ?? B? 6C 00 00 00 66 89 ?? ?? ?? ?? ?? B? 6C 00 00 00 66 89}

    condition:
        all of them
}

rule Gh0stBINS_RDP
{
    meta:
        Author = "Any.Run"
        Date = "2023-06-01"

    strings:
        $pdb = "E:\\MyProjects\\HoldingHands\\Server\\modules\\rd.pdb"

        $str1 = "ClipbdListener" wide
        $str2 = "Try Connect"
        $str3 = "Connect Failed"
        $str4 = "dwTransferBytes:%d"
        $str5 = "m_bManualPost:%d"
        $str6 = "bResult : %d"
        $str7 = "desktop grab failed!" wide
        $str8 = "Register Class Failed!:%d"
        $str9 = "Create Window Failed!:%d"

    condition:
        all of them
}
