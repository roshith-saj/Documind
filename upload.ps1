$filePath = "C:\Users\roshu\OneDrive\Desktop\test.txt"
$fileName = "test.txt"
$boundary = [System.Guid]::NewGuid().ToString()
$fileBytes = [System.IO.File]::ReadAllBytes($filePath)
$fileContent = [System.Text.Encoding]::UTF8.GetString($fileBytes)

$body = "--$boundary`r`n" +
        "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"`r`n" +
        "Content-Type: text/plain`r`n`r`n" +
        "$fileContent`r`n" +
        "--$boundary--"

Invoke-RestMethod -Uri "http://localhost:8080/api/v1/documents/" `
  -Method POST `
  -ContentType "multipart/form-data; boundary=$boundary" `
  -Body $body