high salaries[5] = [1325, 1500, 1485, 1640, 1290];
low size = 5;
high total = 0;
low index = 0;
while(index < size) {
    total = total + salaries[index];
    index = index + 1;
}
low avg = declassify total / size;