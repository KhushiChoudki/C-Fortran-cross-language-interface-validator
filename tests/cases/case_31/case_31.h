struct inner_s { int val; };
struct outer_s { struct inner_s inner; };
void sub_31(struct outer_s s);