# FlyKernel

FlyKernel is optional.

The normal Fly OS ISO deliberately uses Ubuntu's signed generic kernel. That is the safe default for Secure Boot and vendor compatibility.

This directory is for experimenting with a custom kernel package.

## Design rules

- pin an audited upstream stable kernel tag for reproducibility; the normal ISO stays on Ubuntu's signed GA kernel;
- keep patches small;
- never claim an optimization without a repeatable benchmark;
- prefer config changes over invasive scheduler changes;
- keep security mitigations enabled by default;
- do not disable AppArmor, namespaces or kernel hardening just to gain benchmark points.

## Build

On Ubuntu 26.04:

```bash
sudo apt install git build-essential devscripts debhelper libssl-dev libelf-dev \
  dwarves flex bison bc fakeroot
./kernel/build-flykernel.sh
```

The script currently pins upstream Linux **7.2.8** for the experimental package, clones Canonical `ukpack`, applies the tiny Fly identity patch and merges `x86_64_defconfig` with `flykernel.fragment`. Override with `LINUX_TAG=vX.Y.Z` only after testing. The production/default ISO does **not** replace Ubuntu 26.04's signed GA kernel.

## Secure Boot

Self-built packages are not trusted by the normal Ubuntu Secure Boot chain automatically. For real releases, sign the kernel and modules with a project key and document MOK enrollment.


## Modern features, not benchmark hacks

The fragment keeps PSI/cgroups, Landlock, seccomp, AppArmor, NTSYNC and `sched_ext` support available. `sched_ext` support does not mean Fly OS selects an experimental userspace scheduler by default; it is an opt-in research surface. zswap is compiled but default-off because Fly OS already configures zram and avoids pointless double compression. Transparent huge pages use the `madvise` default where supported.
