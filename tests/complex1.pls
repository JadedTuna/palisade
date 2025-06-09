in {
    high salaries[5]: int;
    low size: int;
}
out {
    low avg: int;
}

total := 0;
index := 0;

while (index < size) {
    total = total + salaries[index];
    index = index + 1;
}

avg = declassify total / size;
