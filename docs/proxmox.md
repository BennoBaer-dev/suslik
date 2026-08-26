# Running suslik on Proxmox

suslik does not change on a Proxmox host. Same image, same compose file, same setup wizard as on
any other machine. What changes is one step in front of it: your GPU sits on the Proxmox node, and
it has to arrive inside the container that runs Docker before Docker can hand it to suslik.

This page is one chain per hardware variant. Pick yours and work it top to bottom. Every step says
**where** you type it, what you should see back, and where to go if you see something else. The
chains repeat each other on purpose, so nobody has to assemble their case out of three chapters.

Proxmox details here were checked against the Proxmox VE 9.2 documentation (August 2026). The
`pct set … -dev0 …` commands need **Proxmox VE 8.1 or newer**; the GUI variant arrived in 8.2
("Support device passthrough for containers. The new `dev0`/`dev1`/... options take the path of
host device. … For now, the option cannot be set in the GUI and has to be manually set via API or
CLI." under 8.1, and "Make host device passthrough for containers available in the GUI (issue
754). API and CLI already supported device passthrough since Proxmox VE 8.1." under 8.2,
[Roadmap](https://pve.proxmox.com/wiki/Roadmap)). On older installations there is a second,
low-level route, and every chain that needs it carries it as **Route B**.

## What this page is, and what it is not

This is my own experience, written down so you do not have to repeat it. Everything here was
built and run on my own machines: the Intel chain on a Core Ultra 9 285H with iGPU and NPU, and
the NVIDIA chain on a Proxmox VE 9.2 node with a GeForce RTX 2060, where it ended in
`cuda:0 — device engaged`. Where I have not run something myself, the chain says so, and the
AMD one says it loudly.

What it is not is a guarantee. Your Proxmox, your kernel, your BIOS and your hardware are yours,
and the commands below change your system's configuration, not mine. Read what a command does
before you run it, and keep in mind that a device passed into a container is a device the host
hands out. I cannot promise that any of this works on your machine, and I cannot be responsible
for what it does there.

The purpose is narrow on purpose: to tell you what to set on Proxmox so that a GPU, an NPU or
nothing at all reaches the container that runs suslik. Everything beyond that, how suslik itself
is configured, lives in [installation.md](installation.md).

## Start here

* Intel iGPU, 11th gen Core or newer, with or without an NPU: [Chain 1](#chain-1-intel-igpu-and-npu-gpu-image)
* Older Intel iGPU, HD 5xxx / UHD 6xx on 5th to 10th gen Core: [Chain 2](#chain-2-older-intel-igpus-gpu-legacy-image)
* NVIDIA GPU: [Chain 3](#chain-3-nvidia-cuda-image)
* AMD GPU: [Chain 4](#chain-4-amd-rocm-image-testing)
* No GPU, or just trying it out: [Chain 5](#chain-5-no-gpu-cpu-image)

Your GPU already sits in a VM? Then this page does not apply to you, and
[Pick your chain](#pick-your-chain) says what to do instead. If something already runs and does not
work, [It does not work. Where do I look?](#it-does-not-work-where-do-i-look) sorts the messages by
what you see. Read [Common ground](#common-ground) once before you enter your chain.

## Contents

* [What this page is, and what it is not](#what-this-page-is-and-what-it-is-not)
* [Start here](#start-here)
* [It does not work. Where do I look?](#it-does-not-work-where-do-i-look)
* [Pick your chain](#pick-your-chain)
* [Common ground](#common-ground)
  * [Where you type things](#where-you-type-things)
  * [Why LXC and not a VM](#why-lxc-and-not-a-vm)
  * [The container itself](#the-container-itself)
  * [Disk space](#disk-space)
  * [Two hurdles, not one](#two-hurdles-not-one)
  * [Passing a device node in](#passing-a-device-node-in)
* [Chain 1: Intel iGPU and NPU (gpu image)](#chain-1-intel-igpu-and-npu-gpu-image)
  * [1. Find the render node (on the node)](#1-find-the-render-node-on-the-node)
  * [2. Check for an NPU (on the node)](#2-check-for-an-npu-on-the-node)
  * [3. Hand the nodes into the LXC (on the node)](#3-hand-the-nodes-into-the-lxc-on-the-node)
  * [4. Confirm the first hurdle (in the container)](#4-confirm-the-first-hurdle-in-the-container)
  * [5. Confirm the second hurdle (in the container)](#5-confirm-the-second-hurdle-in-the-container)
  * [6. The compose file (in the container)](#6-the-compose-file-in-the-container)
  * [7. Start it and read the one line that matters (in the container)](#7-start-it-and-read-the-one-line-that-matters-in-the-container)
  * [8. If it says `running on CPU` instead (in the container)](#8-if-it-says-running-on-cpu-instead-in-the-container)
* [Chain 2: older Intel iGPUs (gpu-legacy image)](#chain-2-older-intel-igpus-gpu-legacy-image)
  * [1. Find the render node (on the node)](#1-find-the-render-node-on-the-node-1)
  * [2. Hand the node into the LXC (on the node)](#2-hand-the-node-into-the-lxc-on-the-node)
  * [3. Confirm the first hurdle (in the container)](#3-confirm-the-first-hurdle-in-the-container)
  * [4. Confirm the second hurdle (in the container)](#4-confirm-the-second-hurdle-in-the-container)
  * [5. The compose file (in the container)](#5-the-compose-file-in-the-container)
  * [6. Start it and read the one line (in the container)](#6-start-it-and-read-the-one-line-in-the-container)
  * [7. If it says `running on CPU` instead (in the container)](#7-if-it-says-running-on-cpu-instead-in-the-container)
* [Chain 3: NVIDIA (cuda image)](#chain-3-nvidia-cuda-image)
  * [1. The driver on the node (on the node)](#1-the-driver-on-the-node-on-the-node)
  * [2. Create the device nodes before the LXC starts (on the node)](#2-create-the-device-nodes-before-the-lxc-starts-on-the-node)
  * [3. Hand the nodes into the LXC (on the node)](#3-hand-the-nodes-into-the-lxc-on-the-node-1)
  * [4. The user-space driver inside the container (in the container)](#4-the-user-space-driver-inside-the-container-in-the-container)
  * [5. The Container Toolkit (in the container)](#5-the-container-toolkit-in-the-container)
  * [6. Turn off cgroup enforcement in the toolkit (in the container)](#6-turn-off-cgroup-enforcement-in-the-toolkit-in-the-container)
  * [7. Two smoke tests, because the obvious one is too weak (in the container)](#7-two-smoke-tests-because-the-obvious-one-is-too-weak-in-the-container)
  * [8. The compose file (in the container)](#8-the-compose-file-in-the-container)
  * [9. Start it and read the one line (in the container)](#9-start-it-and-read-the-one-line-in-the-container)
  * [10. If it says something else (in the container)](#10-if-it-says-something-else-in-the-container)
* [Chain 4: AMD (rocm image, testing)](#chain-4-amd-rocm-image-testing)
  * [1. The driver on the node (on the node)](#1-the-driver-on-the-node-on-the-node-1)
  * [2. Find the two devices (on the node)](#2-find-the-two-devices-on-the-node)
  * [3. Hand both into the LXC (on the node)](#3-hand-both-into-the-lxc-on-the-node)
  * [4. Confirm both hurdles (in the container)](#4-confirm-both-hurdles-in-the-container)
  * [5. The compose file (in the container)](#5-the-compose-file-in-the-container-1)
  * [6. Start it and read the one line (in the container)](#6-start-it-and-read-the-one-line-in-the-container-1)
  * [7. If it says `running on CPU` instead (in the container)](#7-if-it-says-running-on-cpu-instead-in-the-container-1)
* [Chain 5: no GPU (cpu image)](#chain-5-no-gpu-cpu-image)
  * [1. Prepare the container (on the node and in the container)](#1-prepare-the-container-on-the-node-and-in-the-container)
  * [2. The compose file (in the container)](#2-the-compose-file-in-the-container)
  * [3. Start it and read the one line (in the container)](#3-start-it-and-read-the-one-line-in-the-container)
  * [4. If suslik mentions a GPU you forgot about (in the container)](#4-if-suslik-mentions-a-gpu-you-forgot-about-in-the-container)
* [Three things that show up later](#three-things-that-show-up-later)

## It does not work. Where do I look?

Left column is what you actually see, in a shell, in the startup log or in the web UI. Right column
is the part of this page that deals with it.

| What you see | Where to look |
|---|---|
| `docker run --rm hello-world` does not print Docker's hello message | [The container itself](#the-container-itself) |
| `docker compose version` errors instead of printing a version | [The container itself](#the-container-itself) |
| The container volume is full, or `DISK LOW` in the log | [Disk space](#disk-space) |
| The device does not show up in the container after `pct set` | [Passing a device node in](#passing-a-device-node-in) |
| A permission error on device passthrough, or the menu entry greyed out | [Passing a device node in](#passing-a-device-node-in) |
| `error gathering device information while adding custom device … no such file or directory` | [Two hurdles, not one](#two-hurdles-not-one) |
| `no such file or directory` in the `docker run` device test | [Two hurdles, not one](#two-hurdles-not-one) |
| `failed to discover GPU vendor from CDI: no known GPU vendor found` | [Two hurdles, not one](#two-hurdles-not-one) |
| `Device <path> does not exist`, the LXC itself does not start | [Two hurdles, not one](#two-hurdles-not-one), [Chain 3, step 2](#2-create-the-device-nodes-before-the-lxc-starts-on-the-node) |
| The container stopped starting after a host reboot | [Chain 3, step 2](#2-create-the-device-nodes-before-the-lxc-starts-on-the-node) |
| `/dev/dri` does not exist on the node | [Chain 1, step 1](#1-find-the-render-node-on-the-node) |
| `running on CPU` on the `gpu` image | [Chain 1, step 8](#8-if-it-says-running-on-cpu-instead-in-the-container) |
| `[ --  ] iGPU  not found` in the self-check | [Chain 1, step 8](#8-if-it-says-running-on-cpu-instead-in-the-container) |
| `found but did NOT bind in real probe — driver/runtime mismatch` | [Chain 1, step 8](#8-if-it-says-running-on-cpu-instead-in-the-container), [Chain 2, step 7](#7-if-it-says-running-on-cpu-instead-in-the-container) |
| `running on CPU` on the `gpu-legacy` image | [Chain 2, step 7](#7-if-it-says-running-on-cpu-instead-in-the-container) |
| `apt install nvidia-driver` would remove `proxmox-ve` | [Chain 3, step 1](#1-the-driver-on-the-node-on-the-node) |
| `'struct vm_area_struct' has no member named '__vm_flags'` while the module builds | [Chain 3, step 1](#1-the-driver-on-the-node-on-the-node) |
| `apt update` on the node fails | [Chain 3, step 1](#1-the-driver-on-the-node-on-the-node) |
| The installer stops on "the availability or presence of an alternate driver installation" | [Chain 3, step 1](#1-the-driver-on-the-node-on-the-node) |
| "nvidia-installer is not able to perform some of the sanity checks" | [Chain 3, step 1](#1-the-driver-on-the-node-on-the-node) |
| "Your kernel headers for kernel ... cannot be found" | [Chain 3, step 1](#1-the-driver-on-the-node-on-the-node) |
| `lspci` does not say `Kernel driver in use: nvidia` | [Chain 3, step 1](#1-the-driver-on-the-node-on-the-node) |
| `nvidia-smi` reports a mismatch between the driver and the kernel module | [Chain 3, step 4](#4-the-user-space-driver-inside-the-container-in-the-container) |
| `Runtimes: io.containerd.runc.v2 runc`, without `nvidia` | [Chain 3, step 5](#5-the-container-toolkit-in-the-container) |
| `nvidia-container-cli: mount error: failed to add device rules: unable to find any existing device filters attached to the cgroup` | [Chain 3, step 6](#6-turn-off-cgroup-enforcement-in-the-toolkit-in-the-container) |
| `nvidia-smi` prints the card, but CUDA is still not detected | [Chain 3, step 7](#7-two-smoke-tests-because-the-obvious-one-is-too-weak-in-the-container) |
| The smoke test prints only `CPUExecutionProvider` | [Chain 3, step 7](#7-two-smoke-tests-because-the-obvious-one-is-too-weak-in-the-container) |
| `could not select device driver "nvidia" with capabilities: [[gpu video]]` | [Chain 3, step 10](#10-if-it-says-something-else-in-the-container) |
| `running on CPU` on the `cuda` image | [Chain 3, step 10](#10-if-it-says-something-else-in-the-container) |
| `Failed to initialize NVML: Unknown Error` | [Chain 3, step 10](#10-if-it-says-something-else-in-the-container) |
| `/dev/kfd` is not there on the node | [Chain 4, step 2](#2-find-the-two-devices-on-the-node) |
| `[warn ] AMD   MIGraphXExecutionProvider available but no /dev/kfd` | [Chain 4, step 7](#7-if-it-says-running-on-cpu-instead-in-the-container-1) |
| `running on CPU` on the `rocm` image | [Chain 4, step 7](#7-if-it-says-running-on-cpu-instead-in-the-container-1) |
| "Found an NVIDIA GPU — the cuda image would use it for recognition." | [Pick your chain](#pick-your-chain) |
| "Found an Intel GPU that this CPU-only image cannot use" | [Chain 5, step 4](#4-if-suslik-mentions-a-gpu-you-forgot-about-in-the-container) |
| "Your data is stored INSIDE the container" | [Three things that show up later](#three-things-that-show-up-later) |

## Pick your chain

| Your hardware | Chain | Image tag |
|---|---|---|
| Intel iGPU (11th gen Core and newer), with or without NPU | [Chain 1](#chain-1-intel-igpu-and-npu-gpu-image) | `latest-gpu` |
| Older Intel iGPU (HD 5xxx / UHD 6xx, 5th to 10th gen Core) | [Chain 2](#chain-2-older-intel-igpus-gpu-legacy-image) | `latest-gpu-legacy` |
| NVIDIA GPU | [Chain 3](#chain-3-nvidia-cuda-image) | `latest-cuda` |
| AMD GPU | [Chain 4](#chain-4-amd-rocm-image-testing) | `latest-rocm` |
| No GPU, or just trying it out | [Chain 5](#chain-5-no-gpu-cpu-image) | `latest-cpu` |

**Two cards in the machine?** suslik runs recognition on one backend, and the image tag decides
which family of hardware that backend can use, so a box with an Intel iGPU and a discrete NVIDIA
card does not use both. Pick the chain for the card you want to run on and pass only that device
in. If a container running the `gpu` image finds no Intel node but an NVIDIA one, the startup
self-check offers you the other way round: "Found an NVIDIA GPU — the cuda image would use it for
recognition."

**Your GPU already sits in a VM?** Then this page does not apply to you. Run suslik as a second
container **inside that same VM**: there the setup is the ordinary one from
[installation.md](installation.md), with no Proxmox step in front of it.

Read [Common ground](#common-ground) once, then go to your chain and stay in it.

## Common ground

### Where you type things

`<ctid>` is your container's numeric ID, the number in front of the name in the Proxmox tree.
`pct list` on the node prints them all ("LXC container index (per node)",
[pct(1)](https://pve.proxmox.com/pve-docs/pct.1.html)). Every command below is marked either
**on the Proxmox node** or **inside the LXC container**, and the marker is the first line of every
code block. Into the container you get with the **Console** button in the Proxmox UI, or from the
node with `pct enter <ctid>` ("Launch a shell for the specified container", pct(1)). A shell on the
node itself is the **Shell** button on the node in the same UI, or SSH to the node. Both are
assumed to be root shells here, which is why no command on this page carries a `sudo`.

The compose file can live anywhere inside the container. The chains below assume a directory you
made for it, `/opt/suslik` in the examples, so the `./suslik-data` line in every compose file means
`/opt/suslik/suslik-data`. Every `docker compose` command runs from that directory:

```bash
# inside the LXC container
mkdir -p /opt/suslik && cd /opt/suslik
```

The starting point for every chain is an LXC created from a Debian or Ubuntu template, with Docker
installed inside it. How to create one is in the
[Proxmox container chapter](https://pve.proxmox.com/pve-docs/chapter-pct.html); this page only
covers what is different afterwards.

### Why LXC and not a VM

An LXC shares the host's kernel, so passing a GPU in means passing a **device node**
(`/dev/dri/renderD128`, `/dev/kfd`, `/dev/nvidia0`) while the card and its driver stay with the
host. Nothing leaves the host in the process, and the same path can be written into a second
container's config as well, which is why Frigate in one container and suslik in another on the
same iGPU is a commonly reported arrangement. I have not measured two containers sharing one
iGPU here, so take that part as reported rather than tested. What the device-node route does fit
is how suslik is built: the image ships the user-space runtime, the kernel driver belongs to the
host (see [hardware-acceleration.md](hardware-acceleration.md)).

A VM works the other way round. Proxmox puts it plainly: "If you 'PCI passthrough' a device, the
device is not available to the host anymore"
([PCI Passthrough](https://pve.proxmox.com/wiki/PCI_Passthrough)). The card leaves the host, so
everything that wants it has to live inside that one VM, and the setup additionally wants a
dedicated IOMMU group per assigned device, the host drivers blacklisted, and interrupt remapping
(the same wiki page documents `allow_unsafe_interrupts` for systems without it). If you go the VM
route anyway, Frigate's documentation adds one warning worth carrying over: disable ballooning on
a VM with a passed-through GPU
([Frigate installation](https://docs.frigate.video/frigate/installation/)).

Two positions from Proxmox belong here, both narrower than they are often quoted. Running Docker
on the node itself is discouraged ("It is not recommended to run docker directly on your Proxmox
VE host"), and the VM recommendation in the same FAQ is conditional: "For use cases requiring
container orchestration or live migration, it is still recommended to run them inside a Proxmox
QEMU virtual machine." ([FAQ](https://pve.proxmox.com/pve-docs/chapter-pve-faq.html)). That
passage is about running Application Containers *as* Proxmox containers (OCI images, a technology
preview in 9.x), not about Docker Engine inside a system LXC, so it does not really cover this
page's case either way. Proxmox does not document Docker in an LXC, and a Proxmox staff member has
advised against it in their own forum: "Running Docker in a container is not recommended at all
due to the way LXC uses layered filesystems (which Docker does also)." (post with a staff badge,
31 March 2023, in
[thread 125066](https://forum.proxmox.com/threads/docker-is-unable-to-access-gpu-in-lxc-gpu-passthrough.125066/)).
That is a forum post rather than documentation, which is why it is quoted here with its date and
its link. This page describes the route because it is the route people ask about and because it
works here, not because Proxmox endorses it.

One limit before you plan around sharing: two containers doing different jobs on one iGPU is the
usual arrangement, but **two suslik instances on one Intel iGPU are not recommended**, because
they can still collide on the device ([known-issues.md](known-issues.md)).

### The container itself

An unprivileged container is Proxmox's default ("This is the default option when creating a new
container", [Proxmox container chapter](https://pve.proxmox.com/pve-docs/chapter-pct.html)) and it
is what the Intel and the NVIDIA chains were run on here. For AMD I have no hardware of my own, so
treat "unprivileged is enough" as reported rather than verified there.

Coming from Frigate, you may bring two habits that this page does not need: a **privileged** LXC
and `privileged: true` in the compose file, or a `chmod 666` on the node's device. The `dev[n]`
route below sets ownership and mode itself, so neither is required here. If you already run them,
nothing breaks; they are just doing no work.

Docker inside a container needs feature flags. Set them in one go:

```bash
# on the Proxmox node
pct config <ctid> | grep features          # read what is already there
pct set <ctid> -features nesting=1,keyctl=1,fuse=1
pct reboot <ctid>
```

Two things about that command. `-features` **replaces the whole feature string**, so any flag you
already had (`mount=nfs`, for instance) has to be listed again or it silently disappears, which is
why you read the current line first. And the change does not reach a running container: `features`
is not hot-pluggable, `pct reboot <ctid>` is what applies it ("Reboot the container by shutting it
down, and starting it again. Applies pending changes.", pct(1)). `pct pending <ctid>` shows
anything still waiting.

Of the three flags, Proxmox documents only `keyctl` as required for Docker: "For unprivileged
containers only: Allow the use of the keyctl() system call. This is required to use docker inside
a container." `nesting` is described as "Allow nesting. Best used with unprivileged containers
with additional id mapping", and `fuse` as "Allow using fuse file systems in a container. Note
that interactions between fuse and the freezer cgroup can potentially cause I/O deadlocks."
([pct.conf(5)](https://pve.proxmox.com/pve-docs/pct.conf.5.html)). `nesting` is common practice
rather than a documented requirement. `fuse` is what Frigate's documentation asks for, with its
own reason ("prevents duplicated files and wasted storage", for the Docker storage driver); note
that Frigate in turn leaves out `keyctl`. Both recipes are incomplete on their own, so the line
above carries all three, and the deadlock caveat is Proxmox's own words, not a footnote I added.

Proof that it took, from inside the container:

```bash
# inside the LXC container
docker run --rm hello-world
docker compose version
```

If the first prints Docker's hello message, `keyctl` and `nesting` are doing their job. If Docker
cannot start at all, check `pct config <ctid> | grep features` on the node and whether the reboot
actually happened. The second has to answer with a version, because every chain below starts suslik
with `docker compose up -d`; if it errors instead, the Compose plugin is missing and wants
installing before you go on.

### Disk space

suslik keeps a clip cache and all learned data in `/data`, and a full container volume is one of
the more common ways to end up with a stuck installation. Growing an LXC disk is one step and
takes effect right away:

```bash
# on the Proxmox node
pct resize <ctid> rootfs +10G
```

`pct resize` grows the volume and the filesystem in it (on a VM, `qm resize` only grows the
virtual disk). The value takes a `+` for a relative increase or a plain number for an absolute
size; shrinking is not supported (pct(1)).

How much you need is not a number this page can invent for you. Two things drive it: the unpacked
image (the CUDA one is several GB larger than the rest) and your clip cache cap. That cap has to
fit on this volume or it can never take effect, and suslik says so at startup when it does not
fit. Check the result from inside:

```bash
# inside the LXC container
df -h /
```

### Two hurdles, not one

This is the part that catches people. Under Proxmox a device crosses **two** boundaries:

1. Proxmox node to LXC container, via a `dev[n]` entry (or the low-level route) in the container config
2. LXC container to Docker container, via `devices:` in your compose file

The compose blocks in [installation.md](installation.md) only cover the second one. Each way of
missing the first has its own signature, and knowing them saves an evening:

* A `devices:` line pointing at a path that does not exist in the LXC: Docker refuses to create
  the container, with `error gathering device information while adding custom device … no such
  file or directory` (measured here, Docker 29.6.1).
* No device line at all: suslik starts and runs on the CPU. Not silently, though. Steps 2 and 3 of
  the startup self-check name the missing device, see the end of each chain.
* The NVIDIA `deploy:` block without a working Container Toolkit: the container is created and
  then start fails with `could not select device driver "nvidia" with capabilities: [[gpu video]]`
  (measured here as well). `docker run --gpus all` fails a bit earlier, with
  `failed to discover GPU vendor from CDI: no known GPU vendor found`.
* A `dev[n]` entry pointing at a path that does not exist **on the node**: the LXC itself does not
  start. pve-container stats the path when it builds the cgroup rules and dies with
  `Device <path> does not exist`. This bites NVIDIA users after a host reboot, see Chain 3, step 2.

The same split applies to numeric GIDs anywhere in your compose file. They are read from the
machine Docker runs on, which under Proxmox is the LXC, never the Proxmox node.

### Passing a device node in

Configuring device passthrough is restricted to **`root@pam`** in Proxmox's own permission check.
A regular Proxmox user with VM privileges gets a permission error, and in the GUI the menu entry
is greyed out.

**In the GUI:** select the container, **Resources → Add → Device Passthrough**, enter the device
path. Owner and mode (`UID in CT`, `GID in CT`, `Access Mode in CT`) sit behind the **Advanced**
switch; left alone, the node arrives as `root:root` with mode `0660`.

**On the command line**, the same thing:

```bash
# on the Proxmox node
pct set <ctid> -dev0 path=/dev/dri/renderD128,mode=0660
```

`dev[n]` is documented in [pct.conf(5)](https://pve.proxmox.com/pve-docs/pct.conf.5.html) with
these sub-options: `path` ("Path to the device to pass through to the container"), `mode`
("Access mode to be set on the device node"), `uid` ("User ID to be assigned to the device node"),
`gid` ("Group ID to be assigned to the device node") and `deny-write`. Number the entries `dev0`,
`dev1` and so on, one per device. `uid=`/`gid=` are the IDs that apply **inside** the container;
Proxmox maps them through the container's ID mapping itself.

One behaviour is worth knowing, and it is read from pve-container's hotplug handling rather than
from the documentation: adding a **new** `dev[n]` reaches a running container immediately, while
changing or removing an existing entry stays pending until the container is rebooted, because the
hotplug code skips over an entry that is already there. Since that is a code reading and not a
documented promise, let `pct pending <ctid>` decide it for your version: whatever it lists is
still waiting, and `pct reboot <ctid>` applies it.

---

## Chain 1: Intel iGPU and NPU (gpu image)

This is the only chain that was run on my own hardware (Core Ultra 9 285H, iGPU plus NPU).

Before step 1: the [Common ground](#common-ground) part is done, that is the feature flags plus the
`pct reboot`, Docker answering inside the container, and enough room on the container volume.

### 1. Find the render node (on the node)

```bash
# on the Proxmox node
ls -l /dev/dri
```

You are looking for an entry named `renderD128`. If there is more than one GPU in the machine you
will also see `renderD129` and up, and the numbering is not guaranteed to survive a reboot, so
identify the card rather than trusting the number:

```bash
# on the Proxmox node
cat /sys/class/drm/renderD128/device/vendor
```

`0x8086` is Intel, `0x10de` NVIDIA, `0x1002` AMD. Every command below writes `renderD128` because
that is the usual name; if your Intel card sits on a different one, use that name in all of them.

If `/dev/dri` does not exist at all, stop here. That is neither a Proxmox nor a suslik problem:
the iGPU is disabled in the BIOS, or the kernel driver did not load. Nothing further down this
chain can help until the node itself shows the node.

### 2. Check for an NPU (on the node)

```bash
# on the Proxmox node
ls -l /dev/accel
```

An `accel0` entry means you have an Intel NPU (Core Ultra chips). If the directory does not exist,
you do not have one; skip every `/dev/accel` line in the rest of this chain, the iGPU alone works.

### 3. Hand the nodes into the LXC (on the node)

**Route A, Proxmox VE 8.1 or newer**, one `dev[n]` entry per device:

```bash
# on the Proxmox node
pct set <ctid> -dev0 path=/dev/dri/renderD128,mode=0660
pct set <ctid> -dev1 path=/dev/accel/accel0,mode=0660      # only if you have an NPU
```

**Route B, installations without `dev[n]`.** This is not a corner case, one of my testers runs
suslik this way. Put these lines into `/etc/pve/lxc/<ctid>.conf` on the node:

```
lxc.cgroup2.devices.allow: c 226:* rwm
lxc.mount.entry: /dev/dri dev/dri none bind,optional,create=dir
```

and make the node readable, because on this route it arrives in the container owned by
`nobody:nogroup` (the host's ownership does not map into an unprivileged container):

```bash
# on the Proxmox node
chmod 666 /dev/dri/renderD128
```

Then `pct reboot <ctid>`. Three honest notes on Route B. Those two keys are LXC's own, not
Proxmox's: `lxc.mount.entry` with its `optional` and `create=dir` options and the generic
`lxc.cgroup2.[controller name]` are documented in
[lxc.container.conf(5)](https://linuxcontainers.org/lxc/manpages/man5/lxc.container.conf.5.html),
and Proxmox documents only that such lines are handed on ("It is also possible to add low-level
LXC-style configuration directly … Those settings are directly passed to the LXC low-level
tools.", [pct.conf(5)](https://pve.proxmox.com/pve-docs/pct.conf.5.html)), not this use of them.
The major number `226` has to match your own node. And the `chmod` does not survive a host reboot
unless you add a udev rule for it. Route A sets ownership and mode itself and needs none of that,
so prefer it if your Proxmox offers it.

Where the major number comes from: `ls -l` prints it for a device node in place of the file size,
as the number before the comma. So `ls -l /dev/dri` gives you the one for the `/dev/dri` line, and
`ls -l /dev/accel` gives you the NPU's, which is a different one. The `/dev/dri` line does not
cover the NPU; on Route B it needs a second `allow` line with its own major and a second
`lxc.mount.entry` for `/dev/accel`.

### 4. Confirm the first hurdle (in the container)

```bash
# inside the LXC container
ls -l /dev/dri
ls -l /dev/accel          # only if you passed an NPU in
```

You should see `renderD128`, and `accel0` if you passed that in too. On Route A it belongs to
`root:root` with mode `0660` (Proxmox's
default when you leave `uid=`/`gid=` alone), on Route B it shows up as `nobody:nogroup` with the
mode you set on the node. Either is fine, they just work differently: read the owner together with
the mode.

If nothing shows up, `pct reboot <ctid>` on the node is the quick answer, and `pct pending <ctid>`
tells you whether something was still waiting.

On Route A, `/dev/dri` inside the container holds only the node you passed in, no `card0` (Route B
bind-mounts the whole directory, so there you see everything the node has). Either way it is
enough: suslik looks for the render node (`renderD*`).

### 5. Confirm the second hurdle (in the container)

Before involving suslik, prove that Docker can hand the node on. Any small image you have will do:

```bash
# inside the LXC container
docker run --rm --device /dev/dri:/dev/dri debian:stable-slim ls -l /dev/dri
```

With an NPU, test that one the same way, because your compose file will pass it as its own device:

```bash
# inside the LXC container
docker run --rm --device /dev/accel/accel0:/dev/accel/accel0 \
  debian:stable-slim ls -l /dev/accel
```

If that lists `renderD128` (and `accel0`), hurdle two is done and anything that goes wrong later is
a driver or runtime question, not a passthrough one. If it fails with `no such file or directory`,
go back to step 4.

### 6. The compose file (in the container)

Everything above this point is passthrough work on the container, and it is the same no matter what runs inside it. If this container is meant for Frigate rather than for suslik, you are done with this page here: carry on with [Frigate's own installation docs](https://docs.frigate.video/frigate/installation/) and give Frigate the same device paths. The compose file below is suslik's.

```yaml
# inside the LXC container: /opt/suslik/compose.yml
services:
  suslik:
    image: ghcr.io/bennobaer-dev/suslik:latest-gpu   # Intel (OpenVINO)
    container_name: suslik
    restart: unless-stopped
    ports:
      - "8199:8199"
    environment:
      - TZ=Europe/Berlin
    devices:
      - "/dev/dri:/dev/dri"                       # iGPU
      - "/dev/accel/accel0:/dev/accel/accel0"     # NPU (omit this line if you have none)
    volumes:
      - ./suslik-data:/data
```

The Intel block in [installation.md](installation.md#intel-variant-igpu--npu-via-openvino) carries
`group_add`, because on an ordinary host the render node belongs to the `render` group. There is
no `group_add` here on purpose: a node passed in with `dev[n]` belongs to `root:root`, so group
membership has nothing to attach to, and suslik's image runs as root anyway (none of the
Dockerfiles set `USER`). If you would rather go by group than by owner, both halves have to match:
append `gid=<render GID inside the container>` to the `dev[n]` line and put that same number into
`group_add`. Read the number with `getent group render video` **inside the container**, and keep
it numeric, group names do not work in `group_add`.

The `volumes:` line is not optional. Without it `/data` lives inside the Docker container and dies
with it on the next recreate.

### 7. Start it and read the one line that matters (in the container)

```bash
# inside the LXC container
docker compose up -d
docker logs -f suslik
```

Let it run rather than grepping three seconds later. On the first start the OpenVINO runtime
compiles its kernels, and on a slow machine the backend line can be minutes away. The self-check
has eight numbered steps and ends with `========== ready ==========`. Ctrl-C leaves the follow, the
container keeps running.

Then the single line that decides it:

```bash
# inside the LXC container
docker logs suslik 2>&1 | grep -m1 -E "device engaged|running on CPU"
```

`openvino:GPU — device engaged` means your iGPU is doing the work. With an NPU as well the line
reads `openvino:MIXED — device engaged (detector=GPU, recognition=NPU)`.

That is the Proxmox part done. The rest is the ordinary first start: open
`http://<container-ip>:8199/` in a browser (`hostname -I` inside the container prints the address)
and the setup wizard walks you through Frigate, cameras and backend
([configuration.md](configuration.md)).

### 8. If it says `running on CPU` instead (in the container)

Step 2 of the same log says which of the two cases you are in:

```
[2/8] hardware   probing accelerators — found + usable? …
         [ ok  ] iGPU  found & usable — device bound in real probe
         [ ok  ] NPU   found & usable — device bound in real probe
```

* `[ --  ] iGPU  not found`: the device never arrived. Back to step 4, then step 3.
* `found but did NOT bind in real probe — driver/runtime mismatch`: it arrived, but the host
  driver and the image's runtime do not line up. suslik names the likely fix itself, in the log
  and as a banner in the web UI: "Your Intel GPU was found but did not bind with this image's
  current Intel runtime. If it is an older iGPU (Intel 6th–10th gen / UHD 6xx), the gpu-legacy
  image supports it; otherwise check the host driver." That banner says 6th to 10th gen, while
  the legacy runtime also covers Gen8 (Broadwell, 5th gen), so read it as the wider range in
  [supported-hardware.md](supported-hardware.md). For an older iGPU, that is
  [Chain 2](#chain-2-older-intel-igpus-gpu-legacy-image). Otherwise the fix is on the Proxmox
  node, because that is where the kernel driver lives; `apt upgrade` inside the LXC cannot change
  it.

Step 3 also prints a direct readout of the first hurdle, with the vendor decoded from the PCI ID,
so a wrong or missing node is visible at a glance:

```
         [info ] GPU render nodes passed through: renderD128=Intel 0x7d51
```

---

## Chain 2: older Intel iGPUs (gpu-legacy image)

For HD 5xxx / UHD 6xx graphics on 5th to 10th gen Core. Intel's current compute runtime only
covers Gen12 and later, so the regular `-gpu` image cannot bind these; the `gpu-legacy` variant
ships Intel's legacy runtime instead. Which generation belongs to which variant is in
[supported-hardware.md](supported-hardware.md). The passthrough is identical to Chain 1. The
differences are the image tag and the absence of an NPU.

Before step 1: the [Common ground](#common-ground) part is done, that is the feature flags plus the
`pct reboot`, Docker answering inside the container, and enough room on the container volume.

### 1. Find the render node (on the node)

```bash
# on the Proxmox node
ls -l /dev/dri
cat /sys/class/drm/renderD128/device/vendor      # 0x8086 = Intel
```

Expect `renderD128`, and the vendor check is worth the second line if there is more than one card
in the machine: `0x8086` is Intel, `0x10de` NVIDIA, `0x1002` AMD. Every command below writes
`renderD128`; if your Intel card sits on a different one, use that name in all of them. Nothing
there at all means the iGPU is off in the BIOS or the kernel driver did not load, and no step below
can compensate for that. These platforms have no NPU, so there is no `/dev/accel` to look for.

### 2. Hand the node into the LXC (on the node)

**Route A, Proxmox VE 8.1 or newer:**

```bash
# on the Proxmox node
pct set <ctid> -dev0 path=/dev/dri/renderD128,mode=0660
```

**Route B, installations without `dev[n]`** (this is the route one of my testers runs). Into
`/etc/pve/lxc/<ctid>.conf`:

```
lxc.cgroup2.devices.allow: c 226:* rwm
lxc.mount.entry: /dev/dri dev/dri none bind,optional,create=dir
```

plus, on the node:

```bash
# on the Proxmox node
chmod 666 /dev/dri/renderD128
```

Check the major number `226` against your own `ls -l /dev/dri`. The `chmod` has to be repeated
after a host reboot unless you make it permanent with a udev rule. Then `pct reboot <ctid>`. The
two keys have the same status as in Chain 1: LXC's own, passed on by Proxmox, and not documented
by Proxmox for this purpose.

### 3. Confirm the first hurdle (in the container)

```bash
# inside the LXC container
ls -l /dev/dri
```

`renderD128` should be listed, `root:root` on Route A, `nobody:nogroup` on Route B. If it says
"No such file or directory", the node is still sitting on the Proxmox host; back to step 2, then
`pct reboot <ctid>`.

### 4. Confirm the second hurdle (in the container)

```bash
# inside the LXC container
docker run --rm --device /dev/dri:/dev/dri debian:stable-slim ls -l /dev/dri
```

Lists `renderD128`, then Docker can pass it on and the rest is a runtime question. If it fails with
`no such file or directory` instead, the node is not in the LXC yet; back to step 3.

### 5. The compose file (in the container)

Everything above this point is passthrough work on the container, and it is the same no matter what runs inside it. If this container is meant for Frigate rather than for suslik, you are done with this page here: carry on with [Frigate's own installation docs](https://docs.frigate.video/frigate/installation/) and give Frigate the same device paths. The compose file below is suslik's.

```yaml
# inside the LXC container: /opt/suslik/compose.yml
services:
  suslik:
    image: ghcr.io/bennobaer-dev/suslik:latest-gpu-legacy   # testing variant
    container_name: suslik
    restart: unless-stopped
    ports:
      - "8199:8199"
    environment:
      - TZ=Europe/Berlin
    devices:
      - "/dev/dri:/dev/dri"                       # iGPU (no /dev/accel: these platforms have no NPU)
    volumes:
      - ./suslik-data:/data
```

As in Chain 1 there is no `group_add`: with `dev[n]` the node belongs to `root:root` and the image
runs as root. If you prefer the group route, set `gid=<render GID inside the container>` on the
`dev[n]` line and put the same number into `group_add`.

`latest-gpu-legacy` follows every release like the other tags, but this variant is not covered by
my own release test machines, so pin a version tag if that matters to you.

### 6. Start it and read the one line (in the container)

```bash
# inside the LXC container
docker compose up -d
docker logs -f suslik      # watch the self-check, Ctrl-C once it says ready
docker logs suslik 2>&1 | grep -m1 -E "device engaged|running on CPU"
```

`openvino:GPU — device engaged` means the legacy runtime bound your iGPU. Give it time on the
first start: the runtime compiles kernels before that line appears, so a grep three seconds after
`up -d` finds nothing and tells you nothing.

Then the Proxmox part is done: open `http://<container-ip>:8199/` in a browser (`hostname -I`
inside the container prints the address) and the setup wizard takes over
([configuration.md](configuration.md)).

### 7. If it says `running on CPU` instead (in the container)

Look at step 2 of the log. `[ --  ] iGPU  not found` sends you back to the passthrough (step 3
above, then step 2). `found but did NOT bind in real probe` on this image means the opposite of Chain 1: suslik
will say "Your Intel GPU was found but did not bind with the legacy runtime — a newer iGPU
(Intel 11th gen or later) needs the regular gpu image." In that case switch the tag to
`latest-gpu` and run Chain 1.

---

## Chain 3: NVIDIA (cuda image)

**An honest word first, because this chain is different from the two above.** NVIDIA documents the
host driver, the Container Toolkit and Docker, and documents none of it inside an LXC container.
Proxmox documents no GPU passthrough into containers either (the pct chapter does not mention
GPUs, the PCI(e) passthrough page does not mention LXC), and Proxmox staff have advised against
Docker in an LXC in their own forum (quoted under [Why LXC and not a VM](#why-lxc-and-not-a-vm)).
The steps below are the Proxmox side plus NVIDIA's own
instructions run in the container, assembled from vendor sources used partly outside their
documented purpose and from community guides that agree with each other.

**Update, 25 August 2026: I have now run this chain myself**, on a Proxmox VE 9.2 node
(kernel 7.0.2-6-pve) with a GeForce RTX 2060, driver 610.57.04, into an unprivileged LXC
running Docker. It works: the suslik startup check reports `cuda:0 — device engaged` and
benchmarks the card at 15.9 ms per inference against 512 ms on the same machine's CPU. The
steps below are what actually worked, including five obstacles that cost me an afternoon and
that no guide had warned me about. They are marked **Trap** where they appear.

There is a route that avoids all of it: if the card is already passed through to a **VM**, run
suslik as a second container in that VM, where the NVIDIA stack sits on the path its vendor
documents. Then follow [installation.md](installation.md#nvidia-variant-cuda) directly and ignore
this page.

Before step 1: the [Common ground](#common-ground) part is done, that is the feature flags plus the
`pct reboot`, Docker answering inside the container, and enough room on the container volume. The
CUDA image is the largest of the five, so the disk section there is not a formality here.

### 1. The driver on the node (on the node)

#### The driver package

The kernel module belongs to the host, so the driver goes on the Proxmox node. Take NVIDIA's own
`.run` package for your card from their driver download rather than a distribution package: step 4
installs that very same file a second time inside the container, and the two have to be the same
version. Put it in `/root` on the node, that is the path the `pct push` in step 4 reads from. The
CUDA runtime baked into the suslik image needs a host driver of **R525 or newer** (details in
[hardware-acceleration.md](hardware-acceleration.md)).

#### Trap 1: Debian's driver packages

**Trap 1: do not install the driver from Debian's packages.** It is the obvious move and it
fails twice over. `apt install nvidia-driver` pulls in packages that would remove `proxmox-ve`,
and Proxmox's own apt hook stops the whole transaction rather than let that happen. And the
version Debian trixie carries (550.163.01) cannot be built against a current Proxmox kernel at
all: the build dies on `'struct vm_area_struct' has no member named '__vm_flags'`, because the
kernel changed that structure after the driver was written. Debian has nothing newer. Take the
`.run` file from NVIDIA.

**Already installed the Debian packages?** Then clear them out before the `.run` file, or its
installer aborts on "the availability or presence of an alternate driver installation". Two things
to watch while you do it. Remove the DKMS module first (`dkms remove nvidia-current/<version>
--all`), because otherwise a dead entry stays behind. And check afterwards that `dkms` itself is
still there: purging `nvidia-*` can take it with it as an unused dependency, and then the `.run`
install fails later with nothing obvious in its output. `apt install dkms build-essential` puts it
back. I ran into exactly this.

#### Trap 2: apt on a fresh Proxmox

**Trap 2: your apt has to work before any of this.** A fresh Proxmox install points at the
enterprise repositories, which need a subscription and make every `apt update` fail. Switch to
the no-subscription repository, and add the `non-free` component if you want any NVIDIA package
at all. Check with `apt update` before you continue; everything below assumes it is clean.

#### The host preparation helper

Proxmox documents a helper for the host preparation on their
[vGPU page](https://pve.proxmox.com/wiki/NVIDIA_vGPU_on_Proxmox_VE): "The `pve-nvidia-vgpu-helper`
tool will set up some basics, like blacklisting the `nouveau` driver, installing header packages,
DKMS and so on."

```bash
# on the Proxmox node
apt install pve-nvidia-vgpu-helper     # only needed below pve-manager 8.3.4, it ships since then
pve-nvidia-vgpu-helper setup
reboot
```

The reboot is what makes the `nouveau` blacklist take effect.

#### Trap 3: nouveau

**Trap 3: without that blacklist the
installer refuses to run**, and its message says so only in the log: "nvidia-installer is not able
to perform some of the sanity checks which detect potential installation problems while Nouveau is
loaded ... (Answer: Abort installation)". If you skip the helper, or if a later cleanup removes the
blacklist file, do it by hand and make sure the module is really gone:

```bash
# on the Proxmox node
printf 'blacklist nouveau\noptions nouveau modeset=0\n' > /etc/modprobe.d/blacklist-nouveau.conf
update-initramfs -u
rmmod nouveau          # or reboot, if it is in use
lsmod | grep nouveau   # must print nothing
```

#### Trap 4: kernel headers

**Trap 4: the headers have to match the running kernel, not the default one.**
`proxmox-default-headers` installs the headers for the current *default* kernel, which is not
necessarily the one you booted. DKMS then fails with "Your kernel headers for kernel ... cannot be
found". `apt install proxmox-headers-$(uname -r)` is the one that always fits. Then the installer, with `--dkms`
("you need to make the installer executable first, and then pass the `--dkms` option when running
it, to ensure that the module is rebuilt after a kernel upgrade", same page):

```bash
# on the Proxmox node
cd /root
chmod +x NVIDIA-Linux-x86_64-<version>.run
./NVIDIA-Linux-x86_64-<version>.run --dkms
```

Two things about where those commands come from. That wiki page is about the **vGPU** driver, so
the file you run is the one you downloaded, not the `-vgpu-kvm` file the page shows in its example.
And if you would rather not hand the preparation to the helper, its documented job is a short list
you can do yourself: blacklist `nouveau`, install kernel headers, install DKMS. Headers on a
Proxmox node do not come from `linux-headers-$(uname -r)`, because the node does not run a Debian
stock kernel; the metapackage is `proxmox-default-headers` ("This is a metapackage which will
install the kernel headers for the default Proxmox kernel series", the package's own description in
the Proxmox repository; note the Administration Guide does not mention it). With Secure Boot on,
the same wiki page has its own section, where the installer runs as `--dkms --skip-module-load`
and the module is built afterwards with `dkms build` and `dkms install`.

**Keep the `.run` file.** You need the exact same one again in step 4.

#### Proof on the node

Proof, on the node:

```bash
# on the Proxmox node
lspci -d 10de: -nnk
```

The line to look for is `Kernel driver in use: nvidia`. If it says `nouveau`, the blacklist has
not taken effect yet, which usually means the node has not been rebooted since the helper ran. If
it names nothing at all, the module did not build or did not load, and the rest of this chain has
nothing to stand on.

### 2. Create the device nodes before the LXC starts (on the node)

#### Why the nodes are not there

This step is the one that surprises people, and it is documented on both sides.

`nvidia_uvm` is not loaded at boot. NVIDIA's
[container wiki](https://nvidia.github.io/container-wiki/toolkit/advanced-usage.html): "the
nvidia_uvm kernel module … is not loaded automatically at boot time, thus /dev/nvidia-uvm is not
created … The kernel module must be manually loaded before starting any CUDA container." The driver README says the same about
`nvidia-uvm.ko` ("generally loaded into the kernel when a CUDA program is started"). And the tool
that would create the nodes on demand, `nvidia-modprobe`, is setuid root and cannot do its job
from inside an unprivileged container.

On the Proxmox side, pve-container stats every `dev[n]` path when it builds the container's cgroup
rules and dies with `Device <path> does not exist` if one is missing. Put those two together and
you get a container that stops starting after every host reboot, because `/dev/nvidia-uvm` is not
there yet.

#### Load the module on the node

So load the module on the node, before the container starts:

```bash
# on the Proxmox node
modprobe nvidia_uvm
nvidia-modprobe -u -c=0
```

and have this happen at every boot.

#### Trap 5: after the next host reboot

**Trap 5, and this is the one that bites after the next
host reboot:** loading the module is not enough. `/etc/modules-load.d/` gets `nvidia_uvm` into the
kernel, but the device node `/dev/nvidia-uvm` still is not created, and a container with a `dev`
entry pointing at it then refuses to start. `nvidia-persistenced` is often named as the fix, but
the `.run` installer does not necessarily give you that service, so do not rely on it either. A
small unit of your own is the reliable way, and it can order itself before the guests:

```bash
# on the Proxmox node
printf 'nvidia\nnvidia_uvm\n' > /etc/modules-load.d/nvidia.conf

cat > /etc/systemd/system/nvidia-nodes.service <<'EOF'
[Unit]
Description=Create NVIDIA device nodes before the containers start
After=local-fs.target
Before=pve-container@.service pve-guests.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/nvidia-modprobe -u -c=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now nvidia-nodes.service
```

This is what I run myself. Verified on my node: right after the driver install only
`/dev/nvidia-caps/nvidia-cap1` existed, and `/dev/nvidia0`, `/dev/nvidiactl`, `/dev/nvidia-uvm`
and `/dev/nvidia-uvm-tools` appeared only after `nvidia-modprobe -u -c=0` ran.

#### What your driver created

Now look at what your driver actually created:

```bash
# on the Proxmox node
ls -l /dev/nvidia*
```

Which nodes exist depends on your driver and card, so work from that output. The list community
guides agree on is `/dev/nvidia0` (or `nvidiaN`), `/dev/nvidiactl`, `/dev/nvidia-modeset`,
`/dev/nvidia-uvm`, `/dev/nvidia-uvm-tools`, and the char devices under `/dev/nvidia-caps/`. NVIDIA
notes that `/dev/nvidia-uvm` and `/dev/nvidiactl` "do not correspond to a GPU and they must be
accessible for all containers".

### 3. Hand the nodes into the LXC (on the node)

**Route A, Proxmox VE 8.1 or newer.** One `dev[n]` entry per node, and `/dev/nvidia-caps/*` needs
its own entries, not the directory:

```bash
# on the Proxmox node, one line per node your ls actually printed
pct set <ctid> -dev0 path=/dev/nvidia0,mode=0660
pct set <ctid> -dev1 path=/dev/nvidiactl,mode=0660
pct set <ctid> -dev2 path=/dev/nvidia-uvm,mode=0660
pct set <ctid> -dev3 path=/dev/nvidia-uvm-tools,mode=0660
# … and so on for the rest of your list
```

**Route B, installations without `dev[n]`** (Proxmox VE 8.0 and older), the same mechanism Chain 1
uses, with one `lxc.mount.entry` per node instead of one `dev[n]`. The major numbers come from
your own listing: for a device node, `ls -l` prints `major, minor` where a regular file has its
size, so read them out of the `ls -l /dev/nvidia*` from step 2. These nodes do not all share one
major, and `/dev/nvidia-uvm` in particular gets a dynamically assigned one, so take every distinct
number your listing shows and write one `allow` line per number. Into `/etc/pve/lxc/<ctid>.conf`:

```
lxc.cgroup2.devices.allow: c <major>:* rwm
lxc.mount.entry: /dev/nvidia0 dev/nvidia0 none bind,optional,create=file
lxc.mount.entry: /dev/nvidiactl dev/nvidiactl none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm dev/nvidia-uvm none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm-tools dev/nvidia-uvm-tools none bind,optional,create=file
```

`/dev/nvidia-caps` is a directory, so if your driver created one it goes in as a directory:
`lxc.mount.entry: /dev/nvidia-caps dev/nvidia-caps none bind,optional,create=dir`. Then make the
nodes readable on the node, because on this route they arrive in an unprivileged container owned
by `nobody:nogroup`, and reboot the container:

```bash
# on the Proxmox node
chmod 666 /dev/nvidia*
pct reboot <ctid>
```

Route B carries the same caveats here as in Chain 1: the keys are LXC's, not Proxmox's, and the
`chmod` is gone after a host reboot unless a udev rule makes it permanent. One caveat is new. I
run Route B on Intel hardware, not on NVIDIA, so the NVIDIA lines above are the mechanism applied
to this device list, not a setup I have seen work. One difference to Route A is worth knowing
here: `optional` means a missing node does not stop the container from starting, so the failure
that step 2 describes (`Device … does not exist` after a host reboot) does not appear on this
route. The node is simply absent instead, and the check below is what tells you.

Check it from inside:

```bash
# inside the LXC container
ls -l /dev/nvidia*
```

Every path you set has to show up here. If the list is empty, `pct reboot <ctid>` on the node and
look again; `pct pending <ctid>` shows whether something is still waiting. If the container refuses
to start with `Device … does not exist`, one of those paths is missing on the node right now. Go
back to step 2.

### 4. The user-space driver inside the container (in the container)

**Not vendor-documented for this case.** NVIDIA's Container Toolkit injects the driver libraries
of the machine it runs on into the container, and under Proxmox that machine is the LXC, not the
node. Without `libnvidia-*` inside the LXC it has nothing to inject. NVIDIA's install guide lists
"Install the NVIDIA GPU driver for your Linux distribution" as a prerequisite, meaning the machine
the toolkit runs on. Several independent community guides plus the community-scripts discussion
for Proxmox agree on the same solution and on its constraint ("for gpu passthrough to work in any
LXC, drivers need to match exactly the host").

The kernel module is already on the node, so install everything except the module in the container,
from the **exact same `.run` file** step 1 left in `/root` on the node:

```bash
# on the Proxmox node
pct push <ctid> /root/NVIDIA-Linux-x86_64-<version>.run /root/NVIDIA-Linux-x86_64-<version>.run
```

```bash
# inside the LXC container
sh /root/NVIDIA-Linux-x86_64-<version>.run --no-kernel-modules
```

NVIDIA's installer describes `--no-kernel-modules` as "Install everything but the kernel modules,
and do not remove any existing, possibly conflicting, kernel modules. … If you use this option,
you must be careful to ensure that NVIDIA kernel modules matching this driver version are
installed separately." That is where the version constraint comes from: the driver in the
container and the module on the node must be the same version. Which also means **every host
driver update makes this step come round again**, on the node and then in the container.

(`--no-kernel-module`, singular, also works; NVIDIA's source marks it as an alias kept for
backwards compatibility, and guides use both spellings.)

Check it inside the container:

```bash
# inside the LXC container
nvidia-smi
```

It should print your card. A complaint about a mismatch between the driver and the kernel module
means exactly what it says: the version in the container is not the version on the node. Install
the same `.run` file in both places. (Keep in mind what this proves and what it does not, see
step 7.)

### 5. The Container Toolkit (in the container)

The toolkit is what hands the driver libraries from step 4 into a Docker container. NVIDIA's
[install guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
has an apt route, and says of it: "These instructions should work for any Debian-derived
distribution." Its own prerequisite, "Install the NVIDIA GPU driver for your Linux distribution",
is what step 4 did, on the machine that counts here. The repository first:

```bash
# inside the LXC container
apt-get update && apt-get install -y --no-install-recommends ca-certificates curl gnupg2
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
apt-get update
```

NVIDIA pins the version on the install line. `1.20.0-1` is the value their guide carried on
25 August 2026, so check the guide for the current one before you copy this:

```bash
# inside the LXC container
export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.20.0-1
apt-get install -y \
    nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
    libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}
```

Then point Docker at it. "The `nvidia-ctk` command modifies the `/etc/docker/daemon.json` file on
the host. The file is updated so that Docker can use the NVIDIA Container Runtime." (same guide),
and the host it means is this container:

```bash
# inside the LXC container
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker
```

(NVIDIA writes all of these lines with `sudo`. Inside the container you are root already, and a
Debian or Ubuntu container template does not necessarily have `sudo` installed, so they are
without it here.)

Proof that it took:

```bash
# inside the LXC container
docker info | grep -i Runtimes
```

The list has to name `nvidia` now. Without the toolkit the same line reads
`Runtimes: io.containerd.runc.v2 runc` (measured here, Docker 29.6.1); if that is still all you
get, either the `nvidia-ctk` call did not reach `/etc/docker/daemon.json` or Docker was not
restarted afterwards.

One thing to know about the ground you are standing on: the toolkit's
[platform support list](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/supported-platforms.html)
covers Debian 11 and several Ubuntu and RHEL releases, and lists neither Debian 12 nor 13, which is
what a current Debian container template is. NVIDIA adds to that table: "Releases can work on more
platforms than indicated in the table above". Together with the Debian-derived sentence quoted at
the top of this step, that is as far as their documentation goes for a Debian 13 template.

### 6. Turn off cgroup enforcement in the toolkit (in the container)

```bash
# inside the LXC container
nvidia-ctk config --set nvidia-container-cli.no-cgroups --in-place
systemctl restart docker
```

**This is the one step where I knowingly use a vendor option outside its documented purpose, so
here is the full picture.** NVIDIA documents this setting only under *Rootless Mode*, and an older
Podman page of theirs warns the other way: "If the user running the containers is a privileged
user (e.g. root) this change should not be made and will cause containers using the NVIDIA
Container Toolkit to fail." The community guides for this setup set it anyway, and the
[Proxmox forum thread](https://forum.proxmox.com/threads/docker-is-unable-to-access-gpu-in-lxc-gpu-passthrough.125066/)
where it gets recommended carries the error it fixes, from inside a nested container:

```
nvidia-container-cli: mount error: failed to add device rules: unable to find any existing device filters attached to the cgroup: bpf_prog_query(BPF_CGROUP_DEVICE) failed: operation not permitted: unknown.
```

Mechanically the option is clear enough: NVIDIA's `libnvidia-container` describes `--no-cgroups`
as "Don't use cgroup enforcement", and under that option it neither looks for nor writes the
devices cgroup, while the bind-mounting of the device nodes carries on. If you see the error line
above, this is the setting it points at. If you do not, you may not need it.

### 7. Two smoke tests, because the obvious one is too weak (in the container)

NVIDIA's own sample workload is:

```bash
# inside the LXC container
docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi
```

Take a printed card as necessary but not sufficient. `nvidia-smi` talks to NVML, which gets by
with `/dev/nvidiactl` and `/dev/nvidia0`, so it prints happily while `/dev/nvidia-uvm` is missing
and CUDA fails afterwards ("`nvidia-smi` works fine but CUDA isn't detected inside the container"
is how a report in NVIDIA's own issue tracker puts it). That is exactly the failure step 2 is
about, and it is the reason this chain has a second test.

First check which nodes actually arrived in the Docker container:

```bash
# inside the LXC container
docker run --rm --runtime=nvidia --gpus all debian:stable-slim \
  ls -l /dev/nvidiactl /dev/nvidia0 /dev/nvidia-uvm /dev/nvidia-uvm-tools
```

Then build a real CUDA context, which is the part `nvidia-smi` never does. The suslik image
carries onnxruntime with the CUDA provider and the recognition model, so it can do this itself:

```bash
# inside the LXC container
docker run --rm --runtime=nvidia --gpus all \
  ghcr.io/bennobaer-dev/suslik:latest-cuda \
  python -c "import onnxruntime as o; s=o.InferenceSession('/app/models/adaface_ir101_webface12m.onnx', providers=['CUDAExecutionProvider']); print(s.get_providers())"
```

The printed list has to contain `CUDAExecutionProvider`. A list with only
`CPUExecutionProvider`, or an error while creating the session, means CUDA did not come up, and
then the compose file below will not fix it either. (This command is built from the image's own
contents. I have run it myself since 25 August 2026, on the RTX 2060 machine described at the
top of this chain.)

### 8. The compose file (in the container)

Everything above this point is passthrough work on the container, and it is the same no matter what runs inside it. If this container is meant for Frigate rather than for suslik, you are done with this page here: carry on with [Frigate's own installation docs](https://docs.frigate.video/frigate/installation/) and give Frigate the same device paths. The compose file below is suslik's.

```yaml
# inside the LXC container: /opt/suslik/compose.yml
services:
  suslik:
    image: ghcr.io/bennobaer-dev/suslik:latest-cuda
    container_name: suslik
    restart: unless-stopped
    ports:
      - "8199:8199"
    environment:
      - TZ=Europe/Berlin
    # GPU passthrough (Compose-spec native, equivalent to `--gpus all`):
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all                          # or device_ids: ["0"] for a specific GPU
              capabilities: [gpu, video]          # `video` enables NVENC clip transcoding
    volumes:
      - ./suslik-data:/data
```

**One open point, stated as such.** With `no-cgroups = true` the toolkit no longer writes device
cgroup rules, and the community sources split on whether `deploy:` alone is then enough: some say
every GPU device has to be listed explicitly, others report `--gpus all` working with no `--device`
at all. None of them is documentation, and I did not keep a citation for either side, so treat
the split itself as the finding. A plausible reading is that some nested cgroups carry
no device filter at all, in which case there is nothing to unblock.

On my own machine the `deploy:` block alone is enough. Checked on 26 August 2026 on the RTX 2060
LXC described at the top of this chain: `no-cgroups = true` is set in
`/etc/nvidia-container-runtime/config.toml`, the running container has no explicit device list at
all (only the `deploy:` request), and recognition runs on `cuda:0`. That is one machine, not a
rule, so keep the other side as a fallback: if the smoke test in step 7 is green but suslik still
does not get the GPU, add the same paths you used in step 3 as an explicit `devices:` block
alongside `deploy:`.

### 9. Start it and read the one line (in the container)

```bash
# inside the LXC container
docker compose up -d
docker logs -f suslik      # watch the self-check, Ctrl-C once it says ready
docker logs suslik 2>&1 | grep -m1 -E "device engaged|running on CPU"
```

`cuda:0 — device engaged` is the answer you want, and unlike `nvidia-smi` it means a real session
was built on the device.

Then the Proxmox part is done: open `http://<container-ip>:8199/` in a browser (`hostname -I`
inside the container prints the address) and the setup wizard takes over
([configuration.md](configuration.md)).

### 10. If it says something else (in the container)

* `could not select device driver "nvidia" with capabilities: [[gpu video]]` at start: the
  Container Toolkit is not in play. Back to steps 5 and 6, and check `/dev/nvidia*` inside the LXC
  (step 3).
* `running on CPU` in the log: read step 2 of the self-check. The line
  `[ ok  ] CUDA  CUDAExecutionProvider available` there means the image's runtime is fine and the
  device is the problem; if that line is missing entirely, you are probably running a different
  image tag than `-cuda`.
* `Failed to initialize NVML: Unknown Error` in a container that worked a minute ago: NVIDIA
  documents this for systems where systemd manages the container's cgroups, where a plain
  `systemctl daemon-reload` is enough to trigger it. Their
  [troubleshooting page](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/troubleshooting.html)
  lists three remedies, of which the cgroup driver one fits this setup best:
  `{"exec-opts": ["native.cgroupdriver=cgroupfs"]}` in `/etc/docker/daemon.json`, then restart
  Docker. The same page notes missing `/dev/char` symlinks as a second trigger with some runc
  versions. The affected container has to be recreated afterwards.
* The container stopped starting after a host reboot: that is the `nvidia_uvm` case from step 2.

---

## Chain 4: AMD (rocm image, testing)

The `-rocm` variant is in its testing phase and has no field confirmation on real AMD hardware
yet, so a CPU fallback is a real possibility here regardless of how well the passthrough goes.
Reports are genuinely welcome ([supported-hardware.md](supported-hardware.md)). I have no AMD
hardware here, so this chain is assembled from AMD's documentation plus the Proxmox
mechanics that the Intel chains proved.

Before step 1: the [Common ground](#common-ground) part is done, that is the feature flags plus the
`pct reboot`, Docker answering inside the container, and enough room on the container volume.

### 1. The driver on the node (on the node)

AMD's kernel-mode driver (`amdgpu-dkms`) goes on the Proxmox node. It is a DKMS package and builds
against the running kernel, so the header note from Chain 3 applies: on a Proxmox node the headers
come from `proxmox-default-headers`, not from `linux-headers-$(uname -r)`. DKMS also means the
module is rebuilt on every kernel update of the node, and a build that fails leaves you without a
GPU after the next reboot, so it is worth a look at `/dev/kfd` after a Proxmox upgrade.

One trap before you start, from AMD's own prerequisites page: "ROCm doesn't currently support
integrated graphics. If your system has an AMD IGP installed, disable it in the BIOS prior to
using ROCm. If the driver can enumerate the IGP, the ROCm runtime might crash the system …"
([Installation prerequisites](https://rocm.docs.amd.com/projects/install-on-linux/en/docs-7.0.0/install/prerequisites.html),
pinned to the ROCm 7.0 docs, because the `latest` version of that page forwards to one that no
longer carries the warning). That matters on any APU plus discrete card machine.

### 2. Find the two devices (on the node)

A ROCm container needs two things: `/dev/kfd`, the compute interface shared by all GPUs, and the
DRI render nodes under `/dev/dri`, one per GPU.

```bash
# on the Proxmox node
ls -l /dev/kfd
ls -l /dev/dri/render*
```

`/dev/kfd` existing is also your proof that the kernel driver loaded. If it is not there, stop
here and fix the driver; nothing below can compensate.

The commands below write `renderD128`. With more than one render node in the list, check which one
is the AMD card and use that name throughout:

```bash
# on the Proxmox node
cat /sys/class/drm/renderD128/device/vendor      # 0x1002 = AMD
```

### 3. Hand both into the LXC (on the node)

**Route A, Proxmox VE 8.1 or newer:**

```bash
# on the Proxmox node
pct set <ctid> -dev0 path=/dev/kfd,mode=0660
pct set <ctid> -dev1 path=/dev/dri/renderD128,mode=0660
```

**Route B, installations without `dev[n]`** (Proxmox VE 8.0 and older), the same mechanism Chain 1
uses. `/dev/kfd` and `/dev/dri` sit on different major numbers, and `ls -l` prints the major for a
device node where a regular file has its size, so read both out of the listing from step 2 and
write one `allow` line each. Into `/etc/pve/lxc/<ctid>.conf`:

```
lxc.cgroup2.devices.allow: c <major of /dev/kfd>:* rwm
lxc.cgroup2.devices.allow: c <major of /dev/dri/renderD128>:* rwm
lxc.mount.entry: /dev/kfd dev/kfd none bind,optional,create=file
lxc.mount.entry: /dev/dri dev/dri none bind,optional,create=dir
```

Then make both readable on the node and reboot the container:

```bash
# on the Proxmox node
chmod 666 /dev/kfd /dev/dri/renderD128
pct reboot <ctid>
```

Same caveats as in Chain 1: the keys are LXC's, not Proxmox's, and the `chmod` is gone after a
host reboot unless a rule makes it permanent, which is what the udev rule below does. And the same
new one as in Chain 3: I run Route B on Intel hardware, so these lines are the mechanism applied
to AMD's device list, not a setup I have seen work.

If permissions rather than presence are the obstacle, AMD documents a udev rule that makes them
persistent instead of re-running `chmod` after every reboot. Into `/etc/udev/rules.d/70-amdgpu.rules`
on the node ([ROCm installation](https://rocm.docs.amd.com/en/latest/install/rocm.html)):

```
KERNEL=="kfd", GROUP="render", MODE="0666"
SUBSYSTEM=="drm", KERNEL=="renderD*", GROUP="render", MODE="0666"
```

followed by `udevadm control --reload-rules` and `udevadm trigger`; AMD adds "To apply
all settings, reboot your system." On their prerequisites page AMD shows the same two lines with a
narrower mode (`MODE="0660"`) and a group you create yourself, written there as `devteam` by way
of example.

### 4. Confirm both hurdles (in the container)

```bash
# inside the LXC container
ls -l /dev/kfd /dev/dri
```

Both have to be listed before Docker can pass them on. If they are not, `pct reboot <ctid>` on the
node, then look again. Then the Docker side:

```bash
# inside the LXC container
docker run --rm --device /dev/kfd:/dev/kfd --device /dev/dri:/dev/dri \
  debian:stable-slim ls -l /dev/kfd /dev/dri
```

Both paths listed again, this time from inside a Docker container, and hurdle two is done. A
`no such file or directory` here means the LXC does not have them yet; back to step 3.

### 5. The compose file (in the container)

Everything above this point is passthrough work on the container, and it is the same no matter what runs inside it. If this container is meant for Frigate rather than for suslik, you are done with this page here: carry on with [Frigate's own installation docs](https://docs.frigate.video/frigate/installation/) and give Frigate the same device paths. The compose file below is suslik's.

```yaml
# inside the LXC container: /opt/suslik/compose.yml
services:
  suslik:
    image: ghcr.io/bennobaer-dev/suslik:latest-rocm   # testing variant
    container_name: suslik
    restart: unless-stopped
    ports:
      - "8199:8199"
    environment:
      - TZ=Europe/Berlin
    devices:
      - "/dev/kfd:/dev/kfd"                       # main compute interface
      - "/dev/dri:/dev/dri"                       # render nodes
    volumes:
      - ./suslik-data:/data
```

As in the Intel chains there is no `group_add`: nodes passed in with `dev[n]` belong to
`root:root`, and the image runs as root. If you went the udev-rule route with a named group
instead, put that group's numeric GID (read **inside the container**) into a `group_add:` list.

### 6. Start it and read the one line (in the container)

```bash
# inside the LXC container
docker compose up -d
docker logs -f suslik      # watch the self-check, Ctrl-C once it says ready
docker logs suslik 2>&1 | grep -m1 -E "device engaged|running on CPU"
```

`migraphx:0 — device engaged` means ROCm bound your card.

Then the Proxmox part is done: open `http://<container-ip>:8199/` in a browser (`hostname -I`
inside the container prints the address) and the setup wizard takes over
([configuration.md](configuration.md)).

### 7. If it says `running on CPU` instead (in the container)

The startup log is unusually specific on this path. Step 2 names the missing piece outright rather
than just reporting a fallback:

```
         [warn ] AMD   MIGraphXExecutionProvider available but no /dev/kfd — pass /dev/kfd + /dev/dri into the container; using CPU
```

That line means hurdle one or two is open, so go back to step 3 and 4. If `/dev/kfd` is present
and it still falls back, you are in the part of the variant that has not been confirmed on real
hardware yet, and an issue with your GPU model genuinely helps.

---

## Chain 5: no GPU (cpu image)

Nothing to pass through, so this chain is short.

### 1. Prepare the container (on the node and in the container)

The [Common ground](#common-ground) steps are all you need: the feature flags plus a `pct reboot`,
Docker inside the container, and enough disk for the clip cache.

```bash
# inside the LXC container
docker run --rm hello-world
docker compose version
df -h /
```

### 2. The compose file (in the container)

Everything above this point is passthrough work on the container, and it is the same no matter what runs inside it. If this container is meant for Frigate rather than for suslik, you are done with this page here: carry on with [Frigate's own installation docs](https://docs.frigate.video/frigate/installation/) and give Frigate the same device paths. The compose file below is suslik's.

```yaml
# inside the LXC container: /opt/suslik/compose.yml
services:
  suslik:
    image: ghcr.io/bennobaer-dev/suslik:latest-cpu
    container_name: suslik
    restart: unless-stopped
    ports:
      - "8199:8199"
    environment:
      - TZ=Europe/Berlin
    volumes:
      - ./suslik-data:/data
```

### 3. Start it and read the one line (in the container)

```bash
# inside the LXC container
docker compose up -d
docker logs -f suslik      # watch the self-check, Ctrl-C once it says ready
docker logs suslik 2>&1 | grep -m1 -E "providers|running on CPU"
```

On the CPU image the backend step of the self-check prints a line that starts with `cpu` and then
lists the execution providers the runtime has. That is the expected result here, not a fallback.

Then open `http://<container-ip>:8199/` in a browser (`hostname -I` inside the container prints the
address) and the setup wizard takes over ([configuration.md](configuration.md)).

### 4. If suslik mentions a GPU you forgot about (in the container)

The self-check also looks the other way round. If it finds a device this image cannot use, it says
so: "Found an Intel GPU that this CPU-only image cannot use — the gpu image (or gpu-legacy for
Intel 6th–10th gen / UHD 6xx) would use it for recognition." In that case pick the matching chain
above; the container itself needs no changes beyond the passthrough and the image tag.

---

## Three things that show up later

**The kernel belongs to the node.** In an LXC there is no kernel of its own, so the kernel and
driver version on the Proxmox node decide whether a device binds. That is why an `apt upgrade`
inside the container never fixes a "found but did NOT bind" line, and why a very new GPU on an
older node may not produce a render node at all. The fix always happens on the node.

**The disk fills up.** The clip cache lives in `/data`, and on a small container volume it hits the
ceiling. `pct resize <ctid> rootfs +10G` on the node is the direct answer. suslik reports its own
limits at startup (`disk limits: cache cap … GB, keep … GB free`), warns when the configured cache
cap is larger than the disk it sits on and therefore can never take effect, and logs `DISK LOW`
when free space drops below its floor.

**Your data disappears on an update.** Not Proxmox-specific, but it happens often enough to
repeat: every compose file needs its `volumes:` entry, otherwise `/data` lives inside the Docker
container and dies with it on the next recreate. suslik warns about this at startup: "Your data is
stored INSIDE the container: /data is not a mounted volume, so people, events and settings are
lost when the container is recreated (e.g. on update)."

Next: [installation.md](installation.md) · [hardware-acceleration.md](hardware-acceleration.md) ·
[supported-hardware.md](supported-hardware.md)
