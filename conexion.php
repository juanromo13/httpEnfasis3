<?php
function conectar()
{
  $user = "root";
  $pass = "";
  $server = "localhost";
  $db = "fitros";
  $con = mysqli_connect($server,$user,$pass) or die ("Error al conectar a la base de datos".mysqli_error());
  mysql_select_db($db,$con);

  return $con;
}
?>
