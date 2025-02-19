<?php
if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    if (isset($_FILES['demo'])) {
        $errors = [];
        $path = 'demos/';
        $extensions = ['dem'];

        $file_name = $_FILES['demo']['name'];
        $file_tmp = $_FILES['demo']['tmp_name'];
        $file_type = $_FILES['demo']['type'];
        $file_ext = strtolower(end(explode('.', $_FILES['demo']['name'])));

        $file = $path . basename($file_name);

        if (!in_array($file_ext, $extensions)) {
            $errors[] = 'Extension not allowed: ' . $file_name . ' ' . $file_type;
        }

        if (empty($errors)) {
            move_uploaded_file($file_tmp, $file);
            echo 'Demo uploaded successfully';
        } else {
            foreach ($errors as $error) {
                echo $error . '<br>';
            }
        }
    }
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>Upload Demo</title>
</head>
<body>
    <form action="upload.php" method="post" enctype="multipart/form-data">
        <input type="file" name="demo" />
        <input type="submit" value="Upload Demo" />
    </form>
</body>
</html>