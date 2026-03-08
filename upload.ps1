$filePath = "C:\Users\roshu\OneDrive\Desktop\test.txt"
$fileName = "test.txt"
$url = "http://43.204.29.38:8080/api/v1/documents/"
$boundary = [System.Guid]::NewGuid().ToString()
$fileBytes = [System.IO.File]::ReadAllBytes($filePath)
$fileContent = [System.Text.Encoding]::UTF8.GetString($fileBytes)

$body = "--$boundary`r`n" +
        "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"`r`n" +
        "Content-Type: text/plain`r`n`r`n" +
        "$fileContent`r`n" +
        "--$boundary--"

Invoke-RestMethod -Uri $url `
  -Method POST `
  -ContentType "multipart/form-data; boundary=$boundary" `
  -Body $body