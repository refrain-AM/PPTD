package main

import (
	"math/big"
	"fmt"
)

func main() {
	keyBits := 512 // length of q1 and q2
	messageSpace := big.NewInt(1021)
	fmt.Println(keyBits,messageSpace)
}
