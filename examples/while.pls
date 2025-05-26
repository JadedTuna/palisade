in {
  high secret: bool;
}
out {
  low done: bool;
}

x := true;
done = false;

while (x) {
  x = secret;
}

x = false;

done = true;