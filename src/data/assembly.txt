@ /F00
LD FIRST
PD 0
LD SECOND
PD 0
LOOP
        LD FIRST
        + SECOND
        MM TEMP
        LD SECOND
        MM FIRST
        LD TEMP
        MM SECOND
        PD 0
        LD SIZE
        - ONE
        JZ FINISH
        MM SIZE
        JP LOOP


FINISH
        OS 0
FIRST    K 0
SECOND   K 1
TEMP     K 0
SIZE     K 12
ONE      K 1
#
