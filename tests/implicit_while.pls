in {
    high secret: int;
}
out {
    low guess: int;
}

guess = 0;
while (guess != secret) {
    guess = guess + 1;
}
