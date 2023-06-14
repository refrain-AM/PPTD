package main

import (
	//"math/big"
	"crypto/rand"
	"github.com/Nik-U/pbc"
	"time"

	//"github.com/sachaservan/bgn"
	"math/big"
)

func main(){
	keyBits:=512
	q1, _ := rand.Prime(rand.Reader, keyBits)
	q2, _ := rand.Prime(rand.Reader, keyBits)

	N:=big.NewInt(0).Mul(q1,q2)
	params := pbc.GenerateA1(N)
	pairing:=pbc.NewPairing(params)
	G1:=pairing.NewG1()
	G2:=pairing.NewG2()
	//GT:=pairing.NewGT()
	Zn:=pairing.NewZr()
	P:=G1.NewFieldElement().Rand()
	P2:=G1.NewFieldElement().Rand()
	Q:=G2.NewFieldElement().Rand()
	//println(P.String())
	//println(Q.String())
	println()
	randzn:=Zn.NewFieldElement().Rand()
	println(randzn.String())
	println(G1.NewFieldElement().MulZn(P,randzn).String())
	println(G1.NewFieldElement().PowZn(P,randzn).String())

	println()
	println(pairing.NewGT().Pair(P,Q).String())
	var startTime,endTime int64

	startTime = time.Now().UnixNano()
	for i:=0;i<100;i++{
		pairing.NewGT().Pair(P,Q)
	}
	endTime = time.Now().UnixNano()
	println(float64(endTime-startTime)/1.0e6/100,"ms")

	startTime = time.Now().UnixNano()
	for i:=0;i<100;i++{
		G1.NewFieldElement().MulZn(P,Zn.NewFieldElement().Rand())
	}
	endTime = time.Now().UnixNano()
	println(float64(endTime-startTime)/1.0e6/100,"ms")

	startTime = time.Now().UnixNano()
	for i:=0;i<100;i++{
		G1.NewFieldElement().PowZn(P,Zn.NewFieldElement().Rand())
	}
	endTime = time.Now().UnixNano()
	println(float64(endTime-startTime)/1.0e6/100,"ms")

	startTime = time.Now().UnixNano()
	for i:=0;i<100;i++{
		G1.NewFieldElement().Add(P,P2)
	}
	endTime = time.Now().UnixNano()
	println(float64(endTime-startTime)/1.0e6/100,"ms")

	startTime = time.Now().UnixNano()
	g:=Zn.NewFieldElement().Rand()
	//println(g.String())
	for i:=0;i<100;i++{
		Zn.NewFieldElement().PowZn(g,Zn.NewFieldElement().Rand())
	}
	endTime = time.Now().UnixNano()
	println(float64(endTime-startTime)/1.0e6/100,"ms")
}
