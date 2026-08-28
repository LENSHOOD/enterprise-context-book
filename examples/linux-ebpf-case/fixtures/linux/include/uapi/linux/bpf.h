enum bpf_cmd {
    BPF_MAP_CREATE,
    BPF_PROG_LOAD,
};

struct bpf_attr {
    int prog_type;
};
