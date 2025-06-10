in {
    high secret: bool;
    high num: int;
}
out {
    high x: bool;
    low y: int;
}

x = true;
x = secret;
x = true || secret;

y = num;
y = 42;
y = 42 + num;
