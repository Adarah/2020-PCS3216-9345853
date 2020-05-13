@   0
START
;; Os 4 primeiros bytes sao metadados. Os 2 primeiros sao o endereco onde o programa deve ser montado
;; O terceiro eh o tamanho do programa
;; O quarto eh o checksum do programa
INICIALIZACAO
            GD  0
            MM GOAL_ONE
            +   NINETY
            MM  POS_ONE
	    -   NINETY
	    MM CHECKSUM
            GD  0
            MM GOAL_TWO
            MM  POS_TWO
	    + CHECKSUM
	    MM CHECKSUM
            GD  0
            MM  LENGTH
	    +  CHECKSUM
	    MM CHECKSUM
	    GD 0
	    MM EXPECTED_SUM
REPEAT
            GD  0               ; 34
            JP  POS_ONE
RETURN
            LD  POS_TWO
            +   ONE
            MM  POS_TWO
            JZ  CARRY
CHECK_IF_DONE
            LD  LENGTH
            -   ONE
            MM  LENGTH
            JZ  VERIFYERROR
            JP  REPEAT          ; 54
CARRY
            LD  POS_ONE
            +   ONE
            MM  POS_ONE
            +   ONE
            JP  CHECK_IF_DONE

POS_ONE     K  00 ;test
POS_TWO     K  00
           +  CHECKSUM
          MM  CHECKSUM
          JP RETURN             ; 72

LENGTH      K  00
ONE         K  01
NINETY      K  /90
CHECKSUM    K 0
EXPECTED_SUM K 0                ;78

VERIFYERROR
	    LD CHECKSUM             ;79
	    - EXPECTED_SUM          ;81
	    JZ FINISH
	    JP ERROR

FINISH

GOAL_ONE    K 0
GOAL_TWO    K 0

ERROR
	    OS 0	
            #  ; comment
