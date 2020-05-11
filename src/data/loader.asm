@   0
START
            GD  0
            MM GOAL_ONE
            +   NINETY
            MM  FIRST_BYTE
            GD  0
            MM GOAL_TWO
            MM  SECOND_BYTE
            GD  0
            MM  LENGTH
REPEAT
            GD  0
            JP  FIRST_BYTE
RETURN
            LD  SECOND_BYTE
            +   ONE
            MM  SECOND_BYTE
            JZ  CARRY
CHECK_IF_DONE
            LD  LENGTH
            -   ONE
            MM  LENGTH
            JZ  FINISH
            JP  REPEAT
CARRY
            LD  FIRST_BYTE
            +   ONE
            MM  FIRST_BYTE
            +   ONE
            JP  CHECK_IF_DONE

FIRST_BYTE   K  00 ;test
SECOND_BYTE  K  00
            JP RETURN
LENGTH        K  00
ONE         K  01
NINETY         K  /90
FINISH
GOAL_ONE    K 0
GOAL_TWO    K 0
            #  ; comment
