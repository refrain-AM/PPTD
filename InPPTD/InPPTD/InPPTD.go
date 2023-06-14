package main

import (
	"encoding/csv"
	"fmt"
	"github.com/sachaservan/paillier"
	"log"
	"math"
	"math/big"
	"math/rand"
	"os"
	"strconv"
	"time"
)

//var gopath = "/home/PPTD/src/PPTDGO"
var gopath = "D:/MyDocuments/Workspace/InPPTD/PPTDGO"

//var gopath = "/home/gopath"

//BGN加密，密文的指数(EMultC)可以是浮点数
// keyBits 是 q1 与 q2 的长度

func init() {
	file := gopath + "/src/InPPTD/" + "InPPTD" + ".txt"
	logFile, err := os.OpenFile(file, os.O_RDWR|os.O_CREATE|os.O_APPEND, 0766)
	if err != nil {
		panic(err)
	}
	log.SetOutput(logFile) // 将文件设置为log输出的文件
	log.SetFlags(log.LstdFlags | log.Lshortfile | log.LUTC)
	return
}

func main() {
	//TestInPPTD()

	//log.Println("--------------------------------")
	//Benchmark(3, 20, 1024, 10)
	//Benchmark(4, 20, 1024, 10)
	//Benchmark(5, 20, 1024, 10)
	//Benchmark(6, 20, 1024, 10)
	//Benchmark(7, 20, 1024, 10)
	//Benchmark(8, 20, 1024, 10)
	//Benchmark(9, 20, 1024, 10)
	//Benchmark(10, 20, 1024, 10)
	log.Println("--------------------------------")

	Benchmark(10, 50, 1024, 10)
	Benchmark(25, 50, 1024, 10)
	Benchmark(50, 50, 1024, 10)
	Benchmark(75, 50, 1024, 10)
	Benchmark(100, 50, 1024, 10)
	Benchmark(125, 50, 1024, 10)
	Benchmark(150, 50, 1024, 10)
	Benchmark(175, 50, 1024, 10)
	Benchmark(200, 50, 1024, 10)
}

func Benchmark(
	workerNumber, objectNumber, keyBits, magnitude int,
) {
	filename := gopath + "/src/normalworkers.csv"
	sp, cp := InitializationPhase(keyBits, magnitude)
	ReportPhase(sp, cp, workerNumber, objectNumber, filename)
	IterationPhase(sp, cp)
	log.Println("InPPTD. K =", workerNumber, ", M =", objectNumber,
		"keyBits =", keyBits*2, "magnitude =",
		magnitude)
	log.Println("sp.ReportPhaseTime =", sp.ReportPhaseTime, "s")
	log.Println("cp.ReportPhaseTime =", cp.ReportPhaseTime, "s")
	log.Println("sp.IterationPhaseTime =", sp.IterationPhaseTime, "s")
	log.Println("cp.IterationPhaseTime =", cp.IterationPhaseTime, "s")
}

func TestInPPTD() {
	workerNumber := 5
	objectNumber := 5
	keyBits := 128
	magnitude := 10
	filename := gopath + "/src/normalworkers.csv"

	sp, cp := InitializationPhase(keyBits, magnitude)
	ReportPhase(sp, cp, workerNumber, objectNumber, filename)
	//fmt.Println("sp.sk.Decrypt(cp.ExKM[k][m])")
	//for k:=0;k<workerNumber;k++{
	//	for m:=0;m<objectNumber;m++{
	//		fmt.Print(sp.sk.Decrypt(cp.ExKM[k][m])," ")
	//	}
	//	fmt.Println()
	//}
	//os.Exit(0)
	fmt.Println("cp.tMfloat64", cp.tMfloat64)
	tMfloat64 := make([]float64, objectNumber, objectNumber)
	tMBigInt := make([]*big.Int, objectNumber, objectNumber)
	copy(tMBigInt, cp.tMBigIntL)
	copy(tMfloat64, cp.tMfloat64)
	fmt.Println("tMfloat64", tMfloat64)

	//for  k:=0;k<workerNumber;k++ {
	//	for m := 0; m < objectNumber; m++ {
	//		fmt.Print(cp.x_KMBigIntL[k][m], "|")
	//	}
	//	fmt.Println()
	//}

	i := 0
	for true {
		IterationPhase(sp, cp)
		fmt.Println(cp.tMfloat64)
		i++
		if convergenceTest(tMBigInt, cp.tMBigIntL, objectNumber, 3, sp.magnitude) {
			break
		}
		copy(tMBigInt, cp.tMBigIntL)
		copy(tMfloat64, cp.tMfloat64)
		fmt.Println(tMfloat64)
	}
	for k := 0; k < 5; k++ {
		IterationPhase(sp, cp)
		fmt.Println(sp.tMfloat64)
	}
	fmt.Printf("迭代次数：%d\n", i)
}

type SP struct {
	pk      *paillier.PublicKey
	sk      *paillier.SecretKey
	keyBits int

	K int
	M int

	rKMfloat64   [][]float64
	rKMBigIntL   [][]*big.Int
	r2KMBigIntL2 [][]*big.Int

	ErKM  [][]*paillier.Ciphertext
	Er2KM [][]*paillier.Ciphertext

	tMfloat64        []float64  //ground truth
	tMBigIntL        []*big.Int //ground truth
	wKMinuxaKBigIntL []*big.Int //perturbed weight for each worker
	wKMinuxaKfloat64 []float64  //perturbed weight for each worker

	magnitude  int
	LBigFloat  *big.Float
	L2BigFloat *big.Float

	ReportPhaseTime    float64
	IterationPhaseTime float64
}

type CP struct {
	pk      *paillier.PublicKey
	keyBits int

	K int
	M int

	x_KMBigIntL   [][]*big.Int
	x_2KMBigIntL2 [][]*big.Int

	ExKM  [][]*paillier.Ciphertext
	Ex2KM [][]*paillier.Ciphertext

	ErKM  [][]*paillier.Ciphertext
	Er2KM [][]*paillier.Ciphertext

	tMfloat64 []float64  //ground truth
	tMBigIntL []*big.Int //ground truth

	aKInt     []int
	aKBigIntL []*big.Int

	magnitude  int
	LBigFloat  *big.Float
	L2BigFloat *big.Float

	ReportPhaseTime    float64
	IterationPhaseTime float64
}

//Initialization Phase 生成密钥
//messageBits is the length of q1 and q2
func InitializationPhase(
	keyBits int,
	magnitude int,
) (
	*SP,
	*CP,
) {
	L := new(big.Float).SetInt(new(big.Int).Exp(big.NewInt(10), big.NewInt(int64(magnitude)), nil))
	L2 := new(big.Float).Mul(L, L)
	sk, pk := paillier.CreateKeyPair(keyBits)

	sp := &SP{
		pk:                 pk,
		sk:                 sk,
		keyBits:            keyBits,
		magnitude:          magnitude,
		LBigFloat:          L,
		L2BigFloat:         L2,
		ReportPhaseTime:    0,
		IterationPhaseTime: 0,
	}

	cp := &CP{
		pk:                 pk,
		keyBits:            keyBits,
		magnitude:          magnitude,
		LBigFloat:          L,
		L2BigFloat:         L2,
		ReportPhaseTime:    0,
		IterationPhaseTime: 0,
	}
	return sp, cp
}

func ReportPhase(sp *SP, cp *CP, K, M int, filename string) {
	ReportPhaseStep1(sp, cp, K, M, filename)
	ReportPhaseStep2(sp, cp)
	ReportPhaseStep3(cp)
}

//数据扰动，worker执行
func ReportPhaseStep1(sp *SP, cp *CP, K, M int, filename string) {
	rand.Seed(time.Now().UnixNano())
	sp.K = K
	cp.K = K
	sp.M = M
	cp.M = M
	xKMfloat64 := InitData(K, M, filename)
	sp.rKMfloat64 = make([][]float64, K, K)
	sp.rKMBigIntL = make([][]*big.Int, K, K)
	sp.r2KMBigIntL2 = make([][]*big.Int, K, K)
	cp.x_KMBigIntL = make([][]*big.Int, K, K)
	cp.x_2KMBigIntL2 = make([][]*big.Int, K, K)

	cp.aKInt = make([]int, K, K)
	cp.aKBigIntL = make([]*big.Int, K, K)
	sp.wKMinuxaKBigIntL = make([]*big.Int, K, K) //perturbed weight for each worker
	sp.wKMinuxaKfloat64 = make([]float64, K, K)

	L := sp.LBigFloat
	L2 := sp.L2BigFloat

	for k := 0; k < K; k++ {
		sp.rKMfloat64[k] = make([]float64, M, M)
		sp.rKMBigIntL[k] = make([]*big.Int, M, M)
		sp.r2KMBigIntL2[k] = make([]*big.Int, M, M)
		cp.x_KMBigIntL[k] = make([]*big.Int, M, M)
		cp.x_2KMBigIntL2[k] = make([]*big.Int, M, M)
		for m := 0; m < M; m++ {
			xkmfloat64 := xKMfloat64[k][m]
			rkmfloat64 := rand.Float64() * xkmfloat64
			sp.rKMfloat64[k][m] = rkmfloat64
			sp.rKMBigIntL[k][m] = float64toBigInt(rkmfloat64, L)
			cp.x_KMBigIntL[k][m] = float64toBigInt(xkmfloat64-rkmfloat64, L)

			x2kmfloat64 := xkmfloat64 * xkmfloat64
			r2kmfloat64 := rand.Float64() * x2kmfloat64
			sp.r2KMBigIntL2[k][m] = float64toBigInt(r2kmfloat64, L2)
			cp.x_2KMBigIntL2[k][m] = float64toBigInt(x2kmfloat64-r2kmfloat64, L2)

			//fmt.Print(cp.x_KMBigIntL[k][m],xkmfloat64-rkmfloat64,float64toBigInt(xkmfloat64-rkmfloat64, L),"|")
		}
		//fmt.Println()
	}

	//TODO 随机初始化 ground truth
	cp.tMfloat64 = make([]float64, M, M)
	cp.tMBigIntL = make([]*big.Int, M, M)
	for m := 0; m < M; m++ {
		cp.tMfloat64[m] = 10.12
		cp.tMBigIntL[m] = float64toBigInt(cp.tMfloat64[m], L)
	}
	sp.tMfloat64 = cp.tMfloat64
	sp.tMBigIntL = cp.tMBigIntL
}

// SP执行
func ReportPhaseStep2(sp *SP, cp *CP) {

	startTime := time.Now().UnixNano()

	pk := sp.pk
	K := sp.K
	M := sp.M
	sp.ErKM = make([][]*paillier.Ciphertext, K, K)
	sp.Er2KM = make([][]*paillier.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		sp.ErKM[k] = make([]*paillier.Ciphertext, M, M)
		sp.Er2KM[k] = make([]*paillier.Ciphertext, M, M)
		for m := 0; m < M; m++ {
			sp.ErKM[k][m] = pk.Encrypt(sp.rKMBigIntL[k][m])
			sp.Er2KM[k][m] = pk.Encrypt(sp.r2KMBigIntL2[k][m])
		}
		//fmt.Println("ReportPhaseStep2, k =", k)
	}

	cp.ErKM = sp.ErKM
	cp.Er2KM = sp.Er2KM

	endTime := time.Now().UnixNano()
	sp.ReportPhaseTime += float64(endTime-startTime) / 1e9

}

// CP执行
func ReportPhaseStep3(cp *CP) {

	startTime := time.Now().UnixNano()

	pk := cp.pk
	K := cp.K
	M := cp.M
	cp.ExKM = make([][]*paillier.Ciphertext, K, K)
	cp.Ex2KM = make([][]*paillier.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		cp.ExKM[k] = make([]*paillier.Ciphertext, M, M)
		cp.Ex2KM[k] = make([]*paillier.Ciphertext, M, M)
		for m := 0; m < M; m++ {
			cp.ExKM[k][m] = pk.EAdd(pk.Encrypt(cp.x_KMBigIntL[k][m]), cp.ErKM[k][m])
			cp.Ex2KM[k][m] = pk.EAdd(pk.Encrypt(cp.x_2KMBigIntL2[k][m]), cp.Er2KM[k][m])

		}
		//fmt.Println("ReportPhaseStep3, k =", k)
	}

	endTime := time.Now().UnixNano()
	cp.ReportPhaseTime += float64(endTime-startTime) / 1e9

}

func IterationPhase(sp *SP, cp *CP) {
	K := cp.K
	M := cp.M
	pk := cp.pk
	sk := sp.sk

	var startTime, endTime int64

	//TODO Weight Estimation

	startTime = time.Now().UnixNano()
	// --------------------------------------------------------
	//TODO PART 1  CP计算
	//公式9. CP computes the secure distance function
	EDistKM := make([][]*paillier.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		EDistKM[k] = make([]*paillier.Ciphertext, M, M)
	}
	for m := 0; m < M; m++ {
		tmBigIntL := cp.tMBigIntL[m]
		t2mBigIntL2 := big.NewInt(0).Mul(tmBigIntL, tmBigIntL)
		bigInt2tm := big.NewInt(0).Mul(big.NewInt(-2), tmBigIntL)
		//bigFloat2tm := big.NewFloat(-2 * tmBigIntL)
		Et2m := pk.Encrypt(t2mBigIntL2)
		for k := 0; k < K; k++ {
			EDistKM[k][m] = pk.EAdd(cp.Ex2KM[k][m], Et2m, pk.ECMult(cp.ExKM[k][m], bigInt2tm))
		}
	}

	//公式10，11. CP聚合distance密文.
	C := pk.Encrypt(paillier.ZERO)
	CK := make([]*paillier.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		CK[k] = pk.Encrypt(paillier.ZERO)
		for m := 0; m < M; m++ {
			CK[k] = pk.EAdd(CK[k], EDistKM[k][m])
		}
		C = pk.EAdd(C, CK[k])
	}

	//CK2 为 Ck'
	CK2 := make([]*paillier.Ciphertext, K, K)
	//CP randomly chooses a random number ak for each worker k
	for k := 0; k < K; k++ {
		//TODO ak的选取，要做的更长的话开销是否更大
		//aKInt[k]=rand.Intn(62)
		cp.aKInt[k] = rand.Intn(int(sp.keyBits/2))
		cp.aKBigIntL[k] = float64toBigInt(float64(cp.aKInt[k]), cp.LBigFloat)
		mantExpak, _ := new(big.Float).SetMantExp(big.NewFloat(1), cp.aKInt[k]).Int(paillier.ZERO)
		CK2[k] = pk.ECMult(CK[k], mantExpak)
	}
	//fmt.Println("ak", cp.aKInt)
	// --------------------------------------------------------
	endTime = time.Now().UnixNano()
	cp.IterationPhaseTime += float64(endTime-startTime) / 1e9

	//CP 发送 C 和 Ck' 给 SP

	startTime = time.Now().UnixNano()
	// --------------------------------------------------------
	//TODO PART 2  SP计算
	DCBigIntL2 := sk.Decrypt(C) //D(C)
	DCBigFloat := new(big.Float).SetInt(DCBigIntL2)
	DCK2BigIntL2 := make([]*big.Int, K, K) //D(Ck')
	for k := 0; k < K; k++ {
		DCK2BigIntL2[k] = sk.Decrypt(CK2[k])
		quo, _ := new(big.Float).Quo(
			DCBigFloat,
			new(big.Float).SetInt(DCK2BigIntL2[k])).Float64()
		sp.wKMinuxaKfloat64[k] = math.Log2(quo)
		sp.wKMinuxaKBigIntL[k] = float64toBigInt(sp.wKMinuxaKfloat64[k], sp.LBigFloat)
		//sp.wKMinuxaKBigIntL[k] ,_ = new(big.Float).Mul(big.NewFloat(sp.wKMinuxaKfloat64[k]), sp.LBigFloat).Int(paillier.ZERO)
	}
	//fmt.Println("wk-ak", sp.wKMinuxaKfloat64)
	//fmt.Println("rmk", sp.rKMfloat64)

	//TODO Truth Estimation
	//To estimate the ground truth, SP first encrypts the perturbed weight(e.g., E(wk − ak))
	EwKMinuxaK := make([]*paillier.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		EwKMinuxaK[k] = pk.Encrypt(sp.wKMinuxaKBigIntL[k])
	}

	ESumKwkMinusakrMk := make([]*paillier.Ciphertext, M, M)
	for m := 0; m < M; m++ {
		SumKwkMinusakrmk := 0.0
		for k := 0; k < K; k++ {
			SumKwkMinusakrmk += (sp.wKMinuxaKfloat64[k] * sp.rKMfloat64[k][m])
		}
		ESumKwkMinusakrMk[m] = pk.Encrypt(float64toBigInt(SumKwkMinusakrmk, sp.L2BigFloat))
	}
	// --------------------------------------------------------
	endTime = time.Now().UnixNano()
	sp.IterationPhaseTime += float64(endTime-startTime) / 1e9

	//SP 发送 E(wk − ak) 给 CP
	//SP 发送 E(sumK(w_k-a_k)r_mk) 给 CP

	startTime = time.Now().UnixNano()
	// --------------------------------------------------------
	//TODO PART3 CP计算
	EwK := make([]*paillier.Ciphertext, K, K)
	//公式13
	ESUMwk := pk.Encrypt(paillier.ZERO)
	for k := 0; k < K; k++ {
		EwK[k] = pk.EAdd(EwKMinuxaK[k], pk.Encrypt(cp.aKBigIntL[k]))
		ESUMwk = pk.EAdd(ESUMwk, EwK[k])
	}
	//公式14
	ESUMwkxkM := make([]*paillier.Ciphertext, M, M)
	//EwKxKM := make([][]*bgn.Ciphertext, K, K)
	//for k := 0; k < K; k++ {
	//	EwKxKM[k] = make([]*bgn.Ciphertext, M, M)
	//}
	ProdExMkak := make([]*paillier.Ciphertext, M, M)
	ProdEwkminusakxMkminusrMk := make([]*paillier.Ciphertext, M, M)
	for m := 0; m < M; m++ {
		ProdExMkak[m] = pk.Encrypt(paillier.ZERO)
		ProdEwkminusakxMkminusrMk[m] = pk.Encrypt(paillier.ZERO)
		for k := 0; k < K; k++ {
			ProdExMkak[m] = pk.EAdd(ProdExMkak[m], pk.ECMult(cp.ExKM[k][m], cp.aKBigIntL[k]))
			//fmt.Println(m, k, sk.Decrypt(ProdExMkak[m]), sk.Decrypt(cp.ExKM[k][m]))
			ProdEwkminusakxMkminusrMk[m] = pk.EAdd(ProdEwkminusakxMkminusrMk[m], pk.ECMult(EwKMinuxaK[k], cp.x_KMBigIntL[k][m]))
		}
		//fmt.Println("!!", sk.Decrypt(ProdExMkak[m]), sk.Decrypt(ESumKwkMinusakrMk[m]), sk.Decrypt(ProdEwkminusakxMkminusrMk[m]))
		ESUMwkxkM[m] = pk.EAdd(ProdExMkak[m], ESumKwkMinusakrMk[m], ProdEwkminusakxMkminusrMk[m])
	}
	// --------------------------------------------------------
	endTime = time.Now().UnixNano()
	cp.IterationPhaseTime += float64(endTime-startTime) / 1e9

	// CP send E(\sum_{k=1}^K{w_k * x_{m,k}}) 和 E(\sum_{k=1}^K{w_k}) to SP

	startTime = time.Now().UnixNano()
	// --------------------------------------------------------
	//TODO PART4 SP计算
	//公式15 更新 Ground Truth
	for m := 0; m < M; m++ {
		SUMwkxkmBigIntL2 := sk.Decrypt(ESUMwkxkM[m])
		//fmt.Println("SUMwkxkmBigIntL2", SUMwkxkmBigIntL2)
		SUMwkBigIntL := sk.Decrypt(ESUMwk)
		//fmt.Println(SUMwkBigIntL.String())
		sp.tMBigIntL[m], _ = new(big.Float).Quo(new(big.Float).SetInt(SUMwkxkmBigIntL2), new(big.Float).SetInt(SUMwkBigIntL)).Int(paillier.ZERO)
		sp.tMfloat64[m] = BigInttofloat64(sp.tMBigIntL[m], sp.LBigFloat)
	}
	// --------------------------------------------------------
	endTime = time.Now().UnixNano()
	sp.IterationPhaseTime += float64(endTime-startTime) / 1e9

}

//TODO Reward Phase
//task i; Pi is the total rewards for task i.
func RewardPhase(sp *SP, cp *CP, Pi float64) (rewards []float64) {
	Si := 0.0
	K := cp.K

	//-------------------------------------
	// CP计算
	for k := 0; k < K; k++ {
		Si += float64(cp.aKInt[k])
	}
	//-------------------------------------

	//-------------------------------------
	// SP计算
	Wi := Si
	for k := 0; k < K; k++ {
		Wi += BigInttofloat64(sp.wKMinuxaKBigIntL[k], sp.LBigFloat)
	}
	psiK := make([]float64, K, K)
	for k := 0; k < K; k++ {
		psiK[k] = BigInttofloat64(sp.wKMinuxaKBigIntL[k], sp.LBigFloat) / Wi * Pi
	}
	//-------------------------------------

	//-------------------------------------
	// CP计算
	pciK := make([]float64, K, K)
	for k := 0; k < K; k++ {
		pciK[k] = float64(cp.aKInt[k]) / Wi * Pi
	}

	rewardK := make([]float64, K, K)
	for k := 0; k < K; k++ {
		rewardK[k] = psiK[k] + pciK[k]
	}
	//-------------------------------------

	return rewardK
}

// K is the number of workers; M is the number of objects.
func InitData(K, M int, filename string) (data [][]float64) {
	f, err := os.Open(filename)
	if err != nil {
		log.Fatalf("can not open file, err is %+v", err)
	}
	r := csv.NewReader(f)
	content, err := r.ReadAll()
	if err != nil {
		log.Fatalf("can not readall, err is %+v", err)
	}
	data = make([][]float64, K, K)
	for k := 0; k < K; k++ {
		row := make([]float64, M, M)
		for m := 0; m < M; m++ {
			row[m], _ = strconv.ParseFloat(content[k][m], 64)
		}
		data[k] = row
	}
	return data
}

func Error(err error) {
	if err != nil {
		panic(err)
	}
}

//检测两数组各元素差异，判断是否收敛
func convergenceTest(x1 []*big.Int, x2 []*big.Int, objectNumber int, accuracy int, magnitude int) bool {
	length := 0
	if magnitude-accuracy > 0 {
		length = magnitude - accuracy
	}
	error := new(big.Int)
	new(big.Float).SetInt(new(big.Int).Exp(big.NewInt(10), big.NewInt(int64(length)), nil)).Int(error)
	//error:=big.NewInt(int64(math.Pow(10,float64(length))))
	for m := 0; m < objectNumber; m++ {
		differ := new(big.Int).Sub(x1[m], x2[m])
		differ.Abs(differ)
		if differ.Cmp(error) >= 0 {
			return false
		}
	}
	return true
}

//L=exp(magnitude)
func float64toBigInt(x float64, L *big.Float) *big.Int {
	xBig, _ := new(big.Float).Mul(big.NewFloat(x), L).Int(paillier.ZERO)
	return xBig
}

func BigInttofloat64(xBig *big.Int, L *big.Float) float64 {
	x, _ := new(big.Float).Quo(new(big.Float).SetInt(xBig), L).Float64()
	return x
}
