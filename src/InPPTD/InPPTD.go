package main

import (
	"encoding/csv"
	"fmt"
	"github.com/sachaservan/bgn"
	"log"
	"math"
	"math/big"
	"math/rand"
	"os"
	"strconv"
	"time"
)

//var gopath = "D:/MyDocuments/Workspace/InPPTD/PPTDGO"
var gopath = "/home/gopath"

//BGN加密，密文的指数(EMultC)可以是浮点数
// keyBits 是 q1 与 q2 的长度


func init() {
	file := gopath+"/src/InPPTD/" + "InPPTD" + ".txt"
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
	Benckmark(5,5,64,10,0.01)

}

func Benckmark(
	workerNumber, objectNumber, keyBits, messageBits int,
	fpPrecision float64,
) {
	filename := gopath+"/src/normalworkers.csv"
	sp, cp := InitializationPhase(keyBits, messageBits, fpPrecision)
	ReportPhase(sp, cp, workerNumber, objectNumber, filename)
	IterationPhase(sp, cp)
	log.Println("InPPTD. K =", workerNumber, ", M =", objectNumber,
		"keyBits =", keyBits, "messageBits =", messageBits, "fpPrecision =",
		fpPrecision)
	log.Println("sp.ReportPhaseTime =", sp.ReportPhaseTime, "s")
	log.Println("cp.ReportPhaseTime =", cp.ReportPhaseTime, "s")
	log.Println("sp.IterationPhaseTime =", sp.IterationPhaseTime, "s")
	log.Println("cp.IterationPhaseTime =", cp.IterationPhaseTime, "s")
}

func TestInPPTD() {
	workerNumber := 5
	objectNumber := 5
	keyBits := 128
	messageBits := 20
	fpPrecision := 0.00001
	filename := gopath+"/src/normalworkers.csv"

	sp, cp := InitializationPhase(keyBits, messageBits, fpPrecision)
	ReportPhase(sp, cp, workerNumber, objectNumber, filename)

	tM := make([]float64, objectNumber, objectNumber)
	copy(tM, cp.tM)
	fmt.Println(tM)

	i := 0
	for true {
		IterationPhase(sp, cp)
		i++
		if convergenceTest(tM, cp.tM, objectNumber, 2) {
			break
		}
		copy(tM, cp.tM)
		fmt.Println(tM)
	}
	fmt.Printf("迭代次数：%d\n", i)
}

type SP struct {
	pk      *bgn.PublicKey
	sk      *bgn.SecretKey
	keyBits int

	K int
	M int

	rKM  [][]float64
	r2KM [][]float64

	ErKM  [][]*bgn.Ciphertext
	Er2KM [][]*bgn.Ciphertext

	tM        []float64 //ground truth
	wKMinuxaK []float64 //perturbed weight for each worker

	ReportPhaseTime    float64
	IterationPhaseTime float64
}

type CP struct {
	pk      *bgn.PublicKey
	keyBits int

	K int
	M int

	x_KM  [][]float64
	x_2KM [][]float64

	ExKM  [][]*bgn.Ciphertext
	Ex2KM [][]*bgn.Ciphertext

	ErKM  [][]*bgn.Ciphertext
	Er2KM [][]*bgn.Ciphertext

	tM []float64 //ground truth

	aK []int

	ReportPhaseTime    float64
	IterationPhaseTime float64
}

//Initialization Phase 生成密钥
//messageBits is the length of q1 and q2
func InitializationPhase(
	keyBits, messageBits int,
	fpPrecision float64, //小数精度
) (
	*SP,
	*CP,
) {
	messageSpace, _ := big.NewFloat(math.Pow(2, float64(messageBits))).Int(new(big.Int))
	fmt.Println("messageSpace =", messageSpace)
	polyBase := 3 // base for the ciphertext polynomial
	fpScaleBase := 3
	//fpPrecision := 0.0001

	pk, sk, _ := bgn.NewKeyGen(keyBits, messageSpace, polyBase, fpScaleBase, fpPrecision, true)

	genG1 := pk.P.NewFieldElement()
	genG1.PowBig(pk.P, sk.Key)

	genGT := pk.Pairing.NewGT().Pair(pk.P, pk.P)
	genGT.PowBig(genGT, sk.Key)
	pk.PrecomputeTables(genG1, genGT)

	sp := &SP{
		pk:                 pk,
		sk:                 sk,
		keyBits:            keyBits,
		ReportPhaseTime:    0,
		IterationPhaseTime: 0,
	}

	cp := &CP{
		pk:                 pk,
		keyBits:            keyBits,
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
	xKM := InitData(K, M, filename)
	sp.rKM = make([][]float64, K, K)
	sp.r2KM = make([][]float64, K, K)
	cp.x_KM = make([][]float64, K, K)
	cp.x_2KM = make([][]float64, K, K)

	cp.aK = make([]int, K, K)
	sp.wKMinuxaK = make([]float64, K, K) //perturbed weight for each worker

	for k := 0; k < K; k++ {
		rkM := make([]float64, M, M)
		r2kM := make([]float64, M, M)
		x_kM := make([]float64, M, M)
		x_2kM := make([]float64, M, M)
		for m := 0; m < M; m++ {
			xkm := xKM[k][m]
			x2km := xkm * xkm
			rkM[m] = rand.Float64() * xkm
			r2kM[m] = rand.Float64() * x2km
			x_kM[m] = xkm - rkM[m]
			x_2kM[m] = x2km - r2kM[m]
		}
		sp.rKM[k] = rkM
		sp.r2KM[k] = r2kM
		cp.x_KM[k] = x_kM
		cp.x_2KM[k] = x_2kM
	}

	//TODO 随机初始化 ground truth
	cp.tM = make([]float64, M, M)
	for m := 0; m < M; m++ {
		cp.tM[m] = 10.12
	}
	sp.tM = cp.tM
}

// SP执行
func ReportPhaseStep2(sp *SP, cp *CP) {

	startTime := time.Now().UnixNano()

	pk := sp.pk
	K := sp.K
	M := sp.M
	sp.ErKM = make([][]*bgn.Ciphertext, K, K)
	sp.Er2KM = make([][]*bgn.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		ErkM := make([]*bgn.Ciphertext, M, M)
		Er2kM := make([]*bgn.Ciphertext, M, M)
		for m := 0; m < M; m++ {
			ErkM[m] = pk.Encrypt(pk.NewPlaintext(big.NewFloat(sp.rKM[k][m])))
			Er2kM[m] = pk.Encrypt(pk.NewPlaintext(big.NewFloat(sp.r2KM[k][m])))
		}
		sp.ErKM[k] = ErkM
		sp.Er2KM[k] = Er2kM
		fmt.Println("ReportPhaseStep2, k =", k)
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
	cp.ExKM = make([][]*bgn.Ciphertext, K, K)
	cp.Ex2KM = make([][]*bgn.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		ExkM := make([]*bgn.Ciphertext, M, M)
		Ex2kM := make([]*bgn.Ciphertext, M, M)
		for m := 0; m < M; m++ {
			ExkM[m] = pk.EAdd(pk.Encrypt(pk.NewPlaintext(big.NewFloat(cp.x_KM[k][m]))), cp.ErKM[k][m])
			Ex2kM[m] = pk.EAdd(pk.Encrypt(pk.NewPlaintext(big.NewFloat(cp.x_2KM[k][m]))), cp.Er2KM[k][m])
		}
		cp.ExKM[k] = ExkM
		cp.Ex2KM[k] = Ex2kM
		fmt.Println("ReportPhaseStep3, k =", k)
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
	EDistKM := make([][]*bgn.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		EDistKM[k] = make([]*bgn.Ciphertext, M, M)
	}
	for m := 0; m < M; m++ {
		tm := cp.tM[m]
		t2m := tm * tm
		bigFloat2tm := big.NewFloat(-2 * tm)
		Et2m := pk.Encrypt(pk.NewPlaintext(big.NewFloat(t2m)))
		for k := 0; k < K; k++ {
			EDistKM[k][m] = pk.EAdd(pk.EAdd(cp.Ex2KM[k][m], Et2m), pk.EMultC(cp.ExKM[k][m], bigFloat2tm))
		}
	}

	//公式10，11. CP聚合distance密文.
	C := pk.Encrypt(pk.NewPlaintext(big.NewFloat(0)))
	CK := make([]*bgn.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		CK[k] = pk.Encrypt(pk.NewPlaintext(big.NewFloat(0)))
		for m := 0; m < M; m++ {
			CK[k] = pk.EAdd(CK[k], EDistKM[k][m])
		}
		C = pk.EAdd(C, CK[k])
	}

	//CK2 为 Ck'
	CK2 := make([]*bgn.Ciphertext, K, K)
	//CP randomly chooses a random number ak for each worker k
	for k := 0; k < K; k++ {
		//TODO ak的选取，要做的更长的话开销是否更大
		//aK[k]=rand.Intn(62)
		cp.aK[k] = rand.Intn(cp.keyBits)
		CK2[k] = pk.EMultC(CK[k], new(big.Float).SetMantExp(big.NewFloat(1), cp.aK[k]))
	}
	// --------------------------------------------------------
	endTime = time.Now().UnixNano()
	cp.IterationPhaseTime += float64(endTime-startTime) / 1e9

	//CP 发送 C 和 Ck' 给 SP

	startTime = time.Now().UnixNano()
	// --------------------------------------------------------
	//TODO PART 2  SP计算
	DCBigFloat := sk.Decrypt(C, pk).PolyEval() //D(C)
	DCK2BigFloat := make([]*big.Float, K, K)   //D(Ck')

	for k := 0; k < K; k++ {
		DCK2BigFloat[k] = sk.Decrypt(CK2[k], pk).PolyEval()
		quo, _ := new(big.Float).Quo(DCBigFloat, DCK2BigFloat[k]).Float64()
		sp.wKMinuxaK[k] = math.Log2(quo)
	}

	//TODO Truth Estimation
	//To estimate the ground truth, SP first encrypts the perturbed weight(e.g., E(wk − ak))
	EwKMinuxaK := make([]*bgn.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		EwKMinuxaK[k] = pk.Encrypt(pk.NewPlaintext(big.NewFloat(sp.wKMinuxaK[k])))
	}
	// --------------------------------------------------------
	endTime = time.Now().UnixNano()
	sp.IterationPhaseTime += float64(endTime-startTime) / 1e9

	//SP 发送 E(wk − ak) 给 CP

	startTime = time.Now().UnixNano()
	// --------------------------------------------------------
	//TODO PART3 CP计算
	EwK := make([]*bgn.Ciphertext, K, K)
	//公式13
	ESUMwk := pk.Encrypt(pk.NewPlaintext(big.NewFloat(0)))
	for k := 0; k < K; k++ {
		EwK[k] = pk.EAdd(EwKMinuxaK[k], pk.Encrypt(pk.NewPlaintext(big.NewFloat(float64(cp.aK[k])))))
		ESUMwk = pk.EAdd(ESUMwk, EwK[k])
	}
	//公式14
	ESUMwkxkM := make([]*bgn.Ciphertext, M, M)
	EwKxKM := make([][]*bgn.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		EwKxKM[k] = make([]*bgn.Ciphertext, M, M)
	}
	for m := 0; m < M; m++ {
		EwKxKM[0][m] = pk.EMult(EwK[0], cp.ExKM[0][m])
		ESUMwkxkM[m] = EwKxKM[0][m].Copy()
		if K > 1 {
			for k := 1; k < K; k++ {
				EwKxKM[k][m] = pk.EMult(EwK[k], cp.ExKM[k][m])
				ESUMwkxkM[m] = pk.EAddL2(ESUMwkxkM[m], EwKxKM[k][m])
			}
		}
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
		SUMwkxkm := sk.Decrypt(ESUMwkxkM[m], pk).PolyEval()
		//fmt.Println(SUMwkxkm.String())
		SUMwk := sk.Decrypt(ESUMwk, pk).PolyEval()
		//fmt.Println(SUMwk.String())
		sp.tM[m], _ = new(big.Float).Quo(SUMwkxkm, SUMwk).Float64()
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
		Si += float64(cp.aK[k])
	}
	//-------------------------------------

	//-------------------------------------
	// SP计算
	Wi := Si
	for k := 0; k < K; k++ {
		Wi += sp.wKMinuxaK[k]
	}
	psiK := make([]float64, K, K)
	for k := 0; k < K; k++ {
		psiK[k] = sp.wKMinuxaK[k] / Wi * Pi
	}
	//-------------------------------------

	//-------------------------------------
	// CP计算
	pciK := make([]float64, K, K)
	for k := 0; k < K; k++ {
		pciK[k] = float64(cp.aK[k]) / Wi * Pi
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
func convergenceTest(x1 []float64, x2 []float64, objectNumber int, accuracy int) bool {
	error := 1 / math.Pow10(accuracy)
	for m := 0; m < objectNumber; m++ {
		if math.Abs(x1[m]-x2[m]) >= error {
			return false
		}
	}
	return true
}
