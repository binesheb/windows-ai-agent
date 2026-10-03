# Surface Book 3 Field Check

Used-laptop diagnostic for the Surface Book 3 configuration discussed: 15-inch, Core i7-1065G7, 32 GB RAM, 1 TB SSD, GTX 1660 Ti 6 GB.

## One command

Run PowerShell as Administrator:

    irm https://raw.githubusercontent.com/binesheb/windows-ai-agent/main/surface-book-3-check/irm.ps1 | iex

The diagnostic checks model/BIOS, CPU, RAM, GPU, display resolution, SSD health, free space, NTFS, battery design/full-charge capacity, battery report, PnP errors, DISM, SFC and recent critical/error events. It also generates a manual checklist for touch, pixels, keyboard, ports, charging, hinge and detach/reattach.

The script is deliberately non-destructive. It does not format disks, change firmware, install drivers or perform write benchmarks.

Battery condition is weighted heavily because Surface Book has separate battery/power components. Microsoft documents design capacity and full-charge capacity as battery-wear indicators and notes that below about 80% is typically battery end-of-life territory.

The output includes a 0-100 health score, a conservative private-sale price ceiling and a verdict. A swollen battery, display lifting, missing GPU, detach failure, intermittent charging, SSD failure or repeated hardware errors overrides the score.
