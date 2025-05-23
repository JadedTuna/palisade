low num = -3; 
low total = 34;
high err = false;
try {
    if(num < 0) {
        throw;
    }
    total = total + num;
} catch {
    err = true;
}