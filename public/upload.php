<?php
if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_FILES['demo'])) {
    $target_dir = "../storage/uploads/";
    $target_file = $target_dir . basename($_FILES["demo"]["name"]);
    move_uploaded_file($_FILES["demo"]["tmp_name"], $target_file);
    echo "The file ". basename( $_FILES["demo"]["name"]). " has been uploaded.";
}
?>
<form action="upload.php" method="post" enctype="multipart/form-data">
    Select demo to upload:
    <input type="file" name="demo" id="demo">
    <input type="submit" value="Upload Demo" name="submit">
</form>