in {
    high pos: int;
}
out {
    low arr[3]: bool;
}

arr[pos] = true;
// arrays can be relabeled low by setting every index to low
arr[0] = false;
arr[1] = false;
arr[2] = false;
