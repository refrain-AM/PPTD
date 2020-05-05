package main

//C. Miao, L. Su, W. Jiang, Y. Li, and M. Tian,
//“A lightweight privacy-preserving truth discovery framework for mobile crowd sensing systems,”
//in Proceedings of 2017 IEEE Conference on Computer Communications (Infocom). IEEE, 2017, pp. 1–9

import (
	"encoding/csv"
	"fmt"
	"github.com/sachaservan/paillier"
	"log"
	"math"
	"os"
	"time"
	//"reflect"
	"strconv"
	// "io"
	"math/big"
	// "github.com/Nik-U/pbc"
)

func init() {
	file := "/home/gopath/src/L2PPTD/" + "L2PPTD" + ".txt"
	logFile, err := os.OpenFile(file, os.O_RDWR|os.O_CREATE|os.O_APPEND, 0766)
	if err != nil {
		panic(err)
	}
	log.SetOutput(logFile) // 将文件设置为log输出的文件
	log.SetFlags(log.LstdFlags | log.Lshortfile | log.LUTC)
	return
}

func main() {
	//TestL2PPTD()
	Benckmark(10, 10, 512, 10)
}

func Benckmark(workerNumber, objectNumber, keybit, magnitude int) {
	filename1 := "/home/gopath/src/normalout1.csv"
	filename2 := "/home/gopath/src/normalout2.csv"
	sa, sb := InitializationPhase(workerNumber, objectNumber,
		filename1, filename2,
		keybit, magnitude)
	OneIteration(sa, sb)
	log.Println("L2PPTD. K =",workerNumber,", M =",objectNumber , "KeyBit =",keybit*2)
	log.Println("sa.InitializationPhaseTime=", sa.InitializationPhaseTime, "s")
	log.Println("sb.InitializationPhaseTime=", sb.InitializationPhaseTime, "s")
	log.Println("sa.IterationPhaseTime=", sa.IterationPhaseTime, "s")
	log.Println("sb.IterationPhaseTime=", sb.IterationPhaseTime, "s")
}

//keybits指的是p、q的长度
//权重小数保留10位(乘10^6)
//所有小数要转化为整数，数据数量级扩大magnitude, 也就是乘上10^magnitude. PPTD中magnitude=10

type SA struct {
	skA                     *paillier.SecretKey
	pkA                     *paillier.PublicKey
	pkB                     *paillier.PublicKey
	K                       int          //workerNumber
	M                       int          //objectNumber
	xkm_Big                 [][]*big.Int //perturbedData
	EAxkm_                  [][]*paillier.Ciphertext
	EBakm                   [][]*paillier.Ciphertext
	Cconti                  []*paillier.Ciphertext
	sumwkBig                *big.Int
	EASumwkxkm              []*paillier.Ciphertext
	InitializationPhaseTime float64 // 单位s
	IterationPhaseTime      float64
	magnitude               int //小数转化成整数所乘上的数量级
	LBigFloat               *big.Float
}

type SB struct {
	skB    *paillier.SecretKey
	pkA    *paillier.PublicKey
	pkB    *paillier.PublicKey
	K      int          //workerNumber
	M      int          //objectNumber
	akmBig [][]*big.Int //randomNumbers
	EAxkm_ [][]*paillier.Ciphertext
	EBakm  [][]*paillier.Ciphertext
	Cconti []*paillier.Ciphertext
	//wk                      []int64
	wkBig                   []*big.Int
	InitializationPhaseTime float64 // 单位s
	IterationPhaseTime      float64
	magnitude               int
	LBigFloat               *big.Float
}

// K is the number of workers; M is the number of objects.
func InitData(K, M int, filename string, magnitude int) [][]*big.Int {
	L := new(big.Float).SetInt(new(big.Int).Exp(big.NewInt(10), big.NewInt(int64(magnitude)), nil))
	//fmt.Println(L)
	f, err := os.Open(filename)
	if err != nil {
		log.Fatalf("can not open file, err is %+v", err)
	}
	r := csv.NewReader(f)
	content, err := r.ReadAll()
	if err != nil {
		log.Fatalf("can not readall, err is %+v", err)
	}
	dataBig := make([][]*big.Int, K, K)
	for k := 0; k < K; k++ {
		row := make([]float64, M, M)
		rowBig := make([]*big.Int, M, M)
		for m := 0; m < M; m++ {
			row[m], _ = strconv.ParseFloat(content[k][m], 64)
			//row[m], _ = strconv.ParseInt(content[k][m], 10, 64)
			bigInt := big.NewInt(0)
			rowBig[m], _ = new(big.Float).Mul(big.NewFloat(row[m]), L).Int(bigInt)
		}
		//fmt.Println(rowBig)
		dataBig[k] = rowBig
	}
	return dataBig
}

//1) Initialization Phase
//generate two servers with their keys, return the objects of SA and SB
// magnitude是小数扩大的数量级，也就是保留的位数，详见PPTD论文
func SystemGen(keyBit, magnitude int) (sa *SA, sb *SB) {
	L := new(big.Float).SetInt(new(big.Int).Exp(big.NewInt(10), big.NewInt(int64(magnitude)), nil))
	sa = new(SA)
	sb = new(SB)
	sa.skA, sa.pkA = paillier.CreateKeyPair(keyBit)
	sb.skB, sb.pkB = paillier.CreateKeyPair(keyBit)
	sb.pkA = sa.pkA
	sa.pkB = sb.pkB
	sa.InitializationPhaseTime = 0
	sa.IterationPhaseTime = 0
	sb.InitializationPhaseTime = 0
	sb.IterationPhaseTime = 0
	sa.magnitude = magnitude
	sb.magnitude = magnitude
	sa.LBigFloat = L
	sb.LBigFloat = L
	return sa, sb
}

//Step I:
func (sa *SA) p1s1(
	K int,
	M int,
	filename string,
) {
	sa.K = K
	sa.M = M
	sa.xkm_Big = InitData(K, M, filename, sa.magnitude)
}

//Step II:
func (sb *SB) p1s2(
	K int,
	M int,
	filename string,
) {
	sb.K = K
	sb.M = M
	sb.akmBig = InitData(K, M, filename, sb.magnitude)
}

//Step III
func (sa *SA) p1s3(sb *SB) {

	startTime := time.Now().UnixNano()

	sa.EAxkm_ = make([][]*paillier.Ciphertext, sa.K, sa.K)
	for index1, row := range sa.xkm_Big {
		sa.EAxkm_[index1] = make([]*paillier.Ciphertext, sa.M, sa.M)
		for index2, m := range row {
			sa.EAxkm_[index1][index2] = sa.pkA.Encrypt(m)
		}
	}

	endTime := time.Now().UnixNano()
	sa.InitializationPhaseTime += float64(endTime-startTime) / 1e9

	sb.EAxkm_ = sa.EAxkm_
}

//Step IV
func (sb *SB) p1s4(sa *SA) {

	startTime := time.Now().UnixNano()

	sb.EBakm = make([][]*paillier.Ciphertext, sb.K, sb.K)
	for index1, row := range sb.akmBig {
		sb.EBakm[index1] = make([]*paillier.Ciphertext, sb.M, sb.M)
		for index2, m := range row {
			sb.EBakm[index1][index2] = sb.pkB.Encrypt(m)
		}
	}

	endTime := time.Now().UnixNano()
	sb.InitializationPhaseTime += float64(endTime-startTime) / 1e9

	sa.EBakm = sb.EBakm
}

func InitializationPhase(
	workerNumber int,
	objectNumber int,
	filename1 string,
	filename2 string,
	keybit int,
	magnitude int,
) (
	sa *SA,
	sb *SB,
) {

	sa, sb = SystemGen(keybit, magnitude)
	sa.p1s1(workerNumber, objectNumber, filename1)
	sb.p1s2(workerNumber, objectNumber, filename2)

	sa.p1s3(sb)
	sb.p1s4(sa)
	return sa, sb
}

//2) Iteration Phase
//step1
func (sa *SA) p2s1(xm []*big.Int, sb *SB) {

	startTime := time.Now().UnixNano()

	K := sa.K
	M := sa.M
	pkB := sa.pkB
	Cconti := make([]*paillier.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		product := pkB.Encrypt(big.NewInt(0))
		for m := 0; m < M; m++ {
			disturbedDistanceSqrt := new(big.Int).Sub(sa.xkm_Big[k][m], xm[m])
			product = pkB.EAdd(
				product,
				pkB.Encrypt(new(big.Int).Mul(disturbedDistanceSqrt, disturbedDistanceSqrt)),
				pkB.ECMult(sa.EBakm[k][m], new(big.Int).Add(disturbedDistanceSqrt, disturbedDistanceSqrt)),
			)
		}
		Cconti[k] = product
	}
	sa.Cconti = Cconti

	endTime := time.Now().UnixNano()
	sa.IterationPhaseTime += float64(endTime-startTime) / 1e9

	sb.Cconti = sa.Cconti
}

func (sb *SB) p2s2() {

	startTime := time.Now().UnixNano()

	K := sb.K
	M := sb.M
	distanceSum := big.NewInt(0)
	distanceSumk := make([]*big.Int, K, K)
	for k := 0; k < K; k++ {
		decryptCconti := sb.skB.Decrypt(sb.Cconti[k])
		sum := big.NewInt(0)
		for m := 0; m < M; m++ {
			sum.Add(sum, new(big.Int).Mul(sb.akmBig[k][m], sb.akmBig[k][m]))
		}
		distanceSumk[k] = new(big.Int).Add(sum, decryptCconti)
		distanceSum.Add(distanceSum, distanceSumk[k])
	}
	//sb.wk = make([]int64, K, K)
	sb.wkBig = make([]*big.Int, K, K)
	distanceSumFloat := big.NewFloat(0).SetInt(distanceSum)
	//magnitude := math.Pow(10, float64(sb.magnitude))
	for k := 0; k < K; k++ {
		quo, _ := big.NewFloat(0).Quo(
			distanceSumFloat,
			big.NewFloat(0).SetInt(distanceSumk[k])).Float64()
		bigInt := new(big.Int)
		sb.wkBig[k], _ = new(big.Float).Mul(big.NewFloat(math.Log(quo)), sb.LBigFloat).Int(bigInt)
		//sb.wk[k] = int64(math.Log(quo) * magnitude)
		//sb.wkBig[k] = big.NewInt(sb.wk[k])
	}

	endTime := time.Now().UnixNano()
	sb.IterationPhaseTime += float64(endTime-startTime) / 1e9
}

func (sb *SB) p2s3(sa *SA) {

	startTime := time.Now().UnixNano()

	K := sb.K
	M := sb.M
	//sumwkakm:=make([]*big.Int,M,M)
	EASumwkxkm := make([]*paillier.Ciphertext, M, M)
	for m := 0; m < M; m++ {
		//临时变量，保存每个m运算结果
		sumwkakmBigInt := big.NewInt(0)
		proEAxkm_wk := sb.pkA.Encrypt(big.NewInt(0))
		for k := 0; k < K; k++ {
			sumwkakmBigInt.Add(
				sumwkakmBigInt,
				new(big.Int).Mul(sb.wkBig[k], sb.akmBig[k][m]),
			)
			proEAxkm_wk = sb.pkA.EAdd(
				proEAxkm_wk,
				sb.pkA.ECMult(sb.EAxkm_[k][m], sb.wkBig[k]),
			)
		}
		//sumwkakm[m]=sumwkakmBigInt
		EASumwkxkm[m] = sb.pkA.EAdd(
			proEAxkm_wk,
			sb.pkA.Encrypt(sumwkakmBigInt),
		)
	}
	sa.EASumwkxkm = EASumwkxkm
	sumwkBig := big.NewInt(0)
	for k := 0; k < K; k++ {
		sumwkBig.Add(sumwkBig, sb.wkBig[k])
	}

	endTime := time.Now().UnixNano()
	sb.IterationPhaseTime += float64(endTime-startTime) / 1e9

	sa.sumwkBig = sumwkBig
}

func (sa *SA) p2s4() []*big.Int {

	startTime := time.Now().UnixNano()

	M := sa.M
	xm := make([]*big.Int, M, M)
	for m := 0; m < M; m++ {
		sumwkxkm := sa.skA.Decrypt(sa.EASumwkxkm[m])
		xmFloat64, _ := big.NewFloat(0).Quo(
			big.NewFloat(0).SetInt(sumwkxkm),
			big.NewFloat(0).SetInt(sa.sumwkBig)).Float64()
		xm[m] = big.NewInt(int64(xmFloat64))
	}

	endTime := time.Now().UnixNano()
	sa.IterationPhaseTime += float64(endTime-startTime) / 1e9

	return xm
}

func printTruthInt(x []*big.Int) {
	for _, xi := range x {
		fmt.Print(xi, " ")
	}
	fmt.Println()
}

func printTruthFloat(x []*big.Float) {
	for _, xi := range x {
		fmt.Print(xi, " ")
	}
	fmt.Println()
}

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

//返回Truth Discovery结果的数组和迭代次数
func IterationPhase(sa *SA, sb *SB, accuracy int) (xm []*big.Float, iterations int) {
	x1 := make([]*big.Int, sa.M, sa.M)
	for i := range x1 {
		//TODO 设置初始值
		x1[i] = big.NewInt(10)
	}
	i := 0
	printTruthInt(x1)
	for true {
		sa.p2s1(x1, sb)
		sb.p2s2()
		sb.p2s3(sa)
		x2 := sa.p2s4()
		printTruthInt(x2)
		i++
		if convergenceTest(x1, x2, sa.M, accuracy, sa.magnitude) {
			break
		}
		x1 = x2
	}
	//L := big.NewFloat(math.Pow(10, float64(sa.magnitude)))
	xm = make([]*big.Float, sa.M, sa.M)
	for i := range xm {
		xm[i] = new(big.Float).Quo(new(big.Float).SetInt(x1[i]), sa.LBigFloat)
	}
	return xm, i
}

func OneIteration(sa *SA, sb *SB) []*big.Int {
	x1 := make([]*big.Int, sa.M, sa.M)
	for i := range x1 {
		x1[i] = big.NewInt(10)
		//TODO 设置初始值
	}
	printTruthInt(x1)
	sa.p2s1(x1, sb)
	sb.p2s2()
	sb.p2s3(sa)
	x2 := sa.p2s4()
	printTruthInt(x2)
	return x2
}

func TestL2PPTD() {
	workerNumber := 10
	objectNumber := 10
	keybit := 1024
	magnitude := 10
	filename1 := "/home/gopath/src/normalout1.csv"
	filename2 := "/home/gopath/src/normalout2.csv"
	sa, sb := InitializationPhase(
		workerNumber, objectNumber,
		filename1, filename2,
		keybit, magnitude)
	xm, iterations := IterationPhase(sa, sb, 3)
	fmt.Println("Result: ")
	printTruthFloat(xm)
	fmt.Println("迭代次数", iterations)
	fmt.Println("sa.InitializationPhaseTime=", sa.InitializationPhaseTime, "s")
	fmt.Println("sb.InitializationPhaseTime=", sb.InitializationPhaseTime, "s")
	fmt.Println("sa.IterationPhaseTime=", sa.IterationPhaseTime/float64(iterations), "s")
	fmt.Println("sb.IterationPhaseTime=", sb.IterationPhaseTime/float64(iterations), "s")
}
