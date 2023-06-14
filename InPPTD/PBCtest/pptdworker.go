package main

import (
	"crypto/rand"
	"math"
	"math/big"
	mathRand "math/rand"
	"time"

	"github.com/sachaservan/paillier"
)

func main()  {
	mathRand.Seed(time.Now().UnixNano())
	K:=10
	M:=100
	p := K + 1
	t := int(math.Floor(float64(p) / 2))
	thresholdKeyGenerator, _ := paillier.GetThresholdKeyGenerator(
		2048, p, t, rand.Reader)
	privateKeys, _ := thresholdKeyGenerator.Generate()
	pk:=privateKeys[0]
	startTime:=time.Now().UnixNano()
	for m:=0;m<M;m++{
		plaintext:=big.NewInt(int64(mathRand.Intn(10000)))
		pk.Encrypt(plaintext)
		if (m+1)%10==0{
			endTime:=time.Now().UnixNano()
			println(m+1,float64(endTime-startTime) / 1e9)
		}
	}


}
