# CastleLoader Config Extractor

Extracts and decrypts configuration strings from CastleLoader malware samples.

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python script.py <memory_dump>
```

## Example
```bash
python script.py castleloader_sample.bin
```

## Requirements
Full memory dump **including PE header** (not partial dumps or shellcode)

## Output
Extracts strings including:
- C2 endpoints
- User-Agent strings
- Mutex names
- Configuration parameters