Manual Verification of AnyDesk 8.0.6 Signing Certificate 
===

Use these steps to manually verify AnyDesk’s certificate 'philandro Software GmbH' (Valid from: 03:12 AM 12.13.2021): 

1. Download and unzip the sample `anydesk-8-0-6.bin` from [the task](https://app.any.run/tasks/d83c85a6-1270-488b-a09d-ad5eac30fae4)

2. Extract the certificate from `anydesk-8-0-6.bin` using the `osslsigncode` utility (or any other convenient utility) 
	```bash
	$ osslsigncode extract-signature -pem -in anydesk-8-0-6.bin -out cert.pem
	Succeeded
	```

3. Specify the analyzed certificate’s serial number via the `openssl` utility
	```bash
	$ openssl pkcs7 -print_certs -text -in cert.pem | grep -A 1 "Serial Number:" | grep -v "Serial Number" | sed 's/://g' | sed 's/^[ \t]*//' | tr -d '\n' | tr -- '-' '\n' | tail -n1 | tr [:lower:] [:upper:]
	0DBF152DEAF0B981A8A938D53F769DB8
	```

4. Download information about the latest changes to the certificates from the Certificate Authority’s official website
	```bash
	$ openssl pkcs7 -print_certs -text -in cert.pem | grep -P -A 2 "CRL Distribution Points" | grep 'URI:' | sed 's/.*URI://' | uniq | xargs -n 1 wget -q
	```

5. Thus, you’ll be able to check the information about the current status of the certificate
	```bash
	$ openssl crl -in DigiCertTrustedG4CodeSigningRSA4096SHA3842021CA1.crl -noout -text | grep --color=always -A 4 0DBF152DEAF0B981A8A938D53F769DB8 | grep -B 4 "Key Compromise"
		Serial Number: 0DBF152DEAF0B981A8A938D53F769DB8
			Revocation Date: Dec 19 00:00:00 2023 GMT
			CRL entry extensions:
				X509v3 CRL Reason Code: 
					Key Compromise
	```
