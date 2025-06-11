in {
	high secret: int;
}
out {
	low x: int;
	low y: int;
}

fn foo(a: int) int { return a; }
fn bar(b: int) int { return foo(b); }

x = bar(10);
y = bar(secret);
