static int bpf_check(struct bpf_attr *attr)
{
    return verifier_prepare(attr);
}

static int bpf_prog_load(struct bpf_attr *attr)
{
    return bpf_check(attr);
}

int __sys_bpf(int cmd, struct bpf_attr *attr)
{
    if (cmd == BPF_PROG_LOAD)
        return bpf_prog_load(attr);
    return 0;
}
