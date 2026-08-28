struct bpf_reg_state {
    int type;
};

static int check_cfg(struct bpf_attr *attr)
{
    return 0;
}

int verifier_prepare(struct bpf_attr *attr)
{
    return check_cfg(attr);
}
