package main

//C. Miao, W. Jiang, L. Su, Y. Li, S. Guo, Z. Qin, H. Xiao, J. Gao, and K. Ren,
//“Cloud-enabled privacy-preserving truth discovery in crowd sensing systems,”
//in Proceedings of the 13th ACM Conference on Embedded Networked Sensor Systems (SenSys). ACM, 2015, pp. 183–196

//使用(p,t)-threshold Paillier cryptosystem ,t=floor(p/2)
//keybits指的是n的长度

import (
	"crypto/rand"
	"encoding/csv"
	"fmt"
	"log"
	"math"
	"math/big"
	mathRand "math/rand"
	"os"
	"strconv"
	"time"

	"github.com/sachaservan/paillier"
	//"reflect"
	// "io"
	// "github.com/Nik-U/pbc"
)

var gopath = "D:/MyDocuments/Workspace/InPPTD/PPTDGO"
//var gopath = "/home/PPTD/src/PPTDGO"

func init() {
	file := gopath + "/src/PPTD/" + "PPTD" + ".txt"
	logFile, err := os.OpenFile(file, os.O_RDWR|os.O_CREATE|os.O_APPEND, 0766)
	if err != nil {
		panic(err)
	}
	log.SetOutput(logFile) // 将文件设置为log输出的文件
	log.SetFlags(log.LstdFlags | log.Lshortfile | log.LUTC)
	return
}

func main() {
	//TestPPTD()
	log.Println("--------------------------------")
	Benchmark(3, 20, 2048, 10)
	Benchmark(4, 20, 2048, 10)
	Benchmark(5, 20, 2048, 10)
	Benchmark(6, 20, 2048, 10)
	Benchmark(7, 20, 2048, 10)
	Benchmark(8, 20, 2048, 10)
	Benchmark(9, 20, 2048, 10)
	Benchmark(10, 20, 2048, 10)

	log.Println("--------------------------------")

	Benchmark(10, 50, 2048, 10)
	Benchmark(25, 50, 2048, 10)
	Benchmark(50, 50, 2048, 10)
	Benchmark(75, 50, 2048, 10)
	Benchmark(100, 50, 2048, 10)
	Benchmark(125, 50, 2048, 10)
	Benchmark(150, 50, 2048, 10)
	Benchmark(175, 50, 2048, 10)
	Benchmark(200, 50, 2048, 10)
}

func Benchmark(userNumber, objectNumber, publicKeyBitLength, magnitude int) {
	filename := gopath + "/src/normalworkers.csv"
	cloud, userGroup := SystemGen(userNumber, objectNumber, filename, publicKeyBitLength, magnitude)

	cloud.step1()

	//一次迭代 step2-6
	cloud.step2(userGroup)
	userGroup.step3(cloud)
	cloud.step4(userGroup)
	userGroup.step5(cloud)
	cloud.step6(userGroup)
	userTimeSum := 0.0
	log.Println("PPTD. K =", userNumber, ", M =", objectNumber, "KeyBit =", publicKeyBitLength)
	log.Println("cloud 用时", cloud.step4time+cloud.step6time+cloud.secureSumTime, "s", "cloud.secureSumDecryptTime=", cloud.secureSumDecryptTime, "s")
	for k := 0; k < userNumber; k++ {
		userTime := userGroup.user[k].step3time + userGroup.user[k].step5time + userGroup.user[k].secureSumTime
		userTimeSum += userTime
		//fmt.Println("user",k,"用时",userTime,"s")
	}
	log.Println("users平均用时", userTimeSum/float64(userNumber), "s")

}

type Cloud struct {
	K          int //userNumber
	M          int //objectNumber
	p          int //TotalNumberOfDecryptionServers
	t          int //threshold, and p is K+1
	privateKey *paillier.ThresholdPrivateKey

	LFloat    float64
	LBigFloat *big.Float //rounding parameter L

	xM []float64 //ground truth

	EpkRounded_DistK    []*paillier.Ciphertext
	EpkRounded_LogDistK []*paillier.Ciphertext
	EpkRounded_wK       []*paillier.Ciphertext
	//ciphertexts of weighted data
	EpkRounded_wKxKM [][]*paillier.Ciphertext

	step4time            float64
	step6time            float64
	secureSumTime        float64
	secureSumDecryptTime float64
}

type User struct {
	id         int //user id
	M          int //objectNumber
	p          int //TotalNumberOfDecryptionServers
	t          int //threshold, and p is K+1
	privateKey *paillier.ThresholdPrivateKey

	LFloat    float64
	LBigFloat *big.Float //rounding parameter L

	xM []float64 //ground truth

	xkM         []float64
	rounded_xkM []*big.Int

	EpkRounded_wk    *paillier.Ciphertext
	EpkRounded_wkxkM []*paillier.Ciphertext

	Ciphertext *paillier.Ciphertext

	step3time     float64
	step5time     float64
	secureSumTime float64
}

type UserGroup struct {
	K    int //userNumber
	user []*User
}

// K is the number of workers; M is the number of objects.
func InitData(
	K, M int, filename string, magnitude int,
) (
	data [][]float64, rounded_data [][]*big.Int,
) {
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
	rounded_data = make([][]*big.Int, K, K)
	LBigFloat := big.NewFloat(math.Pow(10, float64(magnitude)))
	for k := 0; k < K; k++ {
		row := make([]float64, M, M)
		rowBigInt := make([]*big.Int, M, M)
		for m := 0; m < M; m++ {
			row[m], _ = strconv.ParseFloat(content[k][m], 64)
			rowBigInt[m] = roundFloat(row[m], LBigFloat)
		}
		data[k] = row
		rounded_data[k] = rowBigInt
	}
	return data, rounded_data
}

// publicKeyBitLength is the length of n
func SystemGen(
	K, M int,
	filename string,
	publicKeyBitLength, magnitude int,
) (
	cloud *Cloud,
	//user []*User,
	userGroup *UserGroup,
) {
	// 生成 (p-t)门限 Paillier 加密密钥，并将最后一个分配给 cloud
	p := K + 1
	t := int(math.Floor(float64(p) / 2))
	thresholdKeyGenerator, err := paillier.GetThresholdKeyGenerator(
		publicKeyBitLength, p, t, rand.Reader)
	Error(err)
	privateKeys, err := thresholdKeyGenerator.Generate()
	Error(err)
	data, rounded_data := InitData(K, M, filename, magnitude)
	LFloat := math.Pow(10, float64(magnitude))
	cloudServer := &Cloud{
		K:          K,
		M:          M,
		p:          p,
		t:          t,
		privateKey: privateKeys[K],
		LFloat:     LFloat,
		LBigFloat:  big.NewFloat(LFloat),
		//LBigInt:    big.NewInt(int64(LFloat)),
		EpkRounded_DistK:     make([]*paillier.Ciphertext, K, K),
		EpkRounded_LogDistK:  make([]*paillier.Ciphertext, K, K),
		step4time:            0,
		step6time:            0,
		secureSumTime:        0,
		secureSumDecryptTime: 0,
	}
	user := make([]*User, K, K)
	for k := 0; k < K; k++ {
		u := &User{
			id:         k,
			M:          M,
			p:          p,
			t:          t,
			privateKey: privateKeys[k],

			xkM:           data[k],
			rounded_xkM:   rounded_data[k],
			step3time:     0,
			step5time:     0,
			secureSumTime: 0,
		}
		user[k] = u
	}
	userGroup = &UserGroup{
		K:    K,
		user: user,
	}
	return cloudServer, userGroup
}

func (cloud *Cloud) step1() {
	M := cloud.M
	cloud.xM = make([]float64, M, M)
	for m := 0; m < M; m++ {
		// TODO The cloud server S randomly initializes the ground truth for each object
		cloud.xM[m] = 10
	}
}

func (cloud *Cloud) step2(userGroup *UserGroup) {
	K := cloud.K
	for k := 0; k < K; k++ {
		userGroup.user[k].xM = cloud.xM
		userGroup.user[k].LFloat = cloud.LFloat
		userGroup.user[k].LBigFloat = cloud.LBigFloat
	}
}

// TODO step3
func (user *User) step3EachUser(cloud *Cloud) {

	startTime := time.Now().UnixNano()

	M := user.M
	DistkM := make([]float64, M, M)
	Distk := float64(0)
	for m := 0; m < M; m++ {
		DistkM[m] = (user.xkM[m] - user.xM[m]) * (user.xkM[m] - user.xM[m])
		Distk += DistkM[m]
	}
	logDistk := math.Log(Distk)
	rounded_Distk := roundFloat(Distk, user.LBigFloat)
	rounded_LogDistk := roundFloat(logDistk, user.LBigFloat)

	endTime := time.Now().UnixNano()
	user.step3time += float64(endTime-startTime) / 1e9

	cloud.EpkRounded_DistK[user.id] = user.privateKey.Encrypt(rounded_Distk)
	cloud.EpkRounded_LogDistK[user.id] = user.privateKey.Encrypt(rounded_LogDistk)
}

func (userGroup *UserGroup) step3(cloud *Cloud) {
	K := userGroup.K
	for k := 0; k < K; k++ {
		userGroup.user[k].step3EachUser(cloud)
	}
}

func (cloud *Cloud) SecureSumProtocolDecryption(
	encryptedSum *paillier.Ciphertext,
	userGroup *UserGroup,
) (
	sum *big.Int,
) {
	//cloud
	var cloudStartTime, cloudEndTime int64
	cloudStartTime = time.Now().UnixNano()

	t := cloud.t
	K := userGroup.K
	randomlySelectedUsers := generateRandomNumber(0, K, t-1)
	partialDecryptionArray := make([]*paillier.PartialDecryption, t, t)

	cloudEndTime = time.Now().UnixNano()
	cloud.secureSumTime += float64(cloudEndTime-cloudStartTime) / 1e9

	// t-1 users
	for i := range randomlySelectedUsers {

		userStartTime := time.Now().UnixNano()

		partialDecryptionArray[i] = userGroup.user[randomlySelectedUsers[i]].privateKey.Decrypt(encryptedSum.C)

		userEndTime := time.Now().UnixNano()
		userGroup.user[randomlySelectedUsers[i]].secureSumTime += float64(userEndTime-userStartTime) / 1e9
	}

	//cloud
	cloudStartTime = time.Now().UnixNano()

	partialDecryptionArray[t-1] = cloud.privateKey.Decrypt(encryptedSum.C)
	cloud.secureSumDecryptTime += float64(time.Now().UnixNano()-cloudStartTime) / 1e9

	var err error
	sum, err = cloud.privateKey.CombinePartialDecryptions(partialDecryptionArray)
	Error(err)

	cloudEndTime = time.Now().UnixNano()
	cloud.secureSumTime += float64(cloudEndTime-cloudStartTime) / 1e9

	return sum
}

func (cloud *Cloud) step4(userGroup *UserGroup) {

	startTime := time.Now().UnixNano()

	encryptedSumD := cipertextArraySum(cloud.EpkRounded_DistK, cloud.K, cloud.privateKey)
	rounded_SumD := cloud.SecureSumProtocolDecryption(encryptedSumD, userGroup)
	sumD := recoverFloat(rounded_SumD, cloud.LBigFloat)

	//公式15
	logSumD := math.Log(sumD)
	rounded_LogSumD := roundFloat(logSumD, cloud.LBigFloat)
	EpkRounded_LogSumD := cloud.privateKey.Encrypt(rounded_LogSumD)

	//cloud
	K := cloud.K
	cloud.EpkRounded_wK = make([]*paillier.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		cloud.EpkRounded_wK[k] = cloud.privateKey.ESub(EpkRounded_LogSumD, cloud.EpkRounded_LogDistK[k])
	}

	endTime := time.Now().UnixNano()
	cloud.step4time += float64(endTime-startTime) / 1e9

	//the updated ciphertext of weight is sent to each corresponding user;
	for k := 0; k < K; k++ {
		userGroup.user[k].EpkRounded_wk = cloud.EpkRounded_wK[k]
	}
}

func (user *User) step5EachUser(cloud *Cloud) {

	startTime := time.Now().UnixNano()

	M := user.M
	user.EpkRounded_wkxkM = make([]*paillier.Ciphertext, M, M)
	for m := 0; m < M; m++ {
		user.EpkRounded_wkxkM[m] = user.privateKey.ECMult(user.EpkRounded_wk, user.rounded_xkM[m])
	}

	endTime := time.Now().UnixNano()
	user.step5time += float64(endTime-startTime) / 1e9

	cloud.EpkRounded_wKxKM[user.id] = user.EpkRounded_wkxkM
}

func (userGroup *UserGroup) step5(cloud *Cloud) {
	K := userGroup.K
	cloud.EpkRounded_wKxKM = make([][]*paillier.Ciphertext, K, K)
	for k := 0; k < K; k++ {
		userGroup.user[k].step5EachUser(cloud)
	}
}

func (cloud *Cloud) step6(userGroup *UserGroup) {

	var startTime, endTime int64
	startTime = time.Now().UnixNano()

	K := cloud.K
	M := cloud.M
	key := cloud.privateKey
	L2 := new(big.Float).Mul(cloud.LBigFloat, cloud.LBigFloat)

	EpkEounded_Sumwk := cipertextArraySum(cloud.EpkRounded_wK, K, key)
	sum_wk := recoverFloat(cloud.SecureSumProtocolDecryption(EpkEounded_Sumwk, userGroup), cloud.LBigFloat)

	endTime = time.Now().UnixNano()
	cloud.step6time += float64(endTime-startTime) / 1e9

	for m := 0; m < M; m++ {

		startTime = time.Now().UnixNano()

		sumRounded_wKxKM := key.Encrypt(big.NewInt(0))
		for k := 0; k < K; k++ {
			sumRounded_wKxKM = key.EAdd(sumRounded_wKxKM, cloud.EpkRounded_wKxKM[k][m])
		}

		endTime = time.Now().UnixNano()
		cloud.step6time += float64(endTime-startTime) / 1e9

		sum_wKxKM := cloud.SecureSumProtocolDecryption(sumRounded_wKxKM, userGroup)
		cloud.xM[m] = recoverFloat(sum_wKxKM, L2) / sum_wk
	}
}

func TestPPTD() {
	userNumber := 10
	objectNumber := 10
	publicKeyBitLength := 2048
	magnitude := 10
	filename := gopath + "/src/normalworkers.csv"
	cloud, userGroup := SystemGen(userNumber, objectNumber, filename, publicKeyBitLength, magnitude)
	cloud.step1()

	xM := make([]float64, objectNumber, objectNumber)

	copy(xM, cloud.xM)
	fmt.Println(xM)
	i := 0
	for true {
		cloud.step2(userGroup)
		userGroup.step3(cloud)
		//fmt.Println(cloud)
		cloud.step4(userGroup)
		userGroup.step5(cloud)
		cloud.step6(userGroup)
		i++
		if convergenceTest(xM, cloud.xM, objectNumber, 3) {
			break
		}
		copy(xM, cloud.xM)
		fmt.Println(xM)
	}
	fmt.Printf("迭代次数：%d\n", i)
}

func roundFloat(x float64, LBigFloat *big.Float) *big.Int {
	bigInt := big.NewInt(0)
	rounded_x, _ := new(big.Float).Mul(big.NewFloat(x), LBigFloat).Int(bigInt)
	return rounded_x
}

func recoverFloat(rounded_x *big.Int, LBigFloat *big.Float) float64 {
	xFloat64, _ := new(big.Float).Quo(new(big.Float).SetInt(rounded_x), LBigFloat).Float64()
	return xFloat64
}

func Error(err error) {
	if err != nil {
		panic(err)
	}
}

//生成count个[start,end)结束的不重复的随机数
func generateRandomNumber(start int, end int, count int) []int {
	//范围检查
	if end < start || (end-start) < count {
		return nil
	}

	//存放结果的slice
	nums := make([]int, 0)
	//随机数生成器，加入时间戳保证每次生成的随机数不一样
	r := mathRand.New(mathRand.NewSource(time.Now().UnixNano()))
	for len(nums) < count {
		//生成随机数
		num := r.Intn((end - start)) + start
		//查重
		exist := false
		for _, v := range nums {
			if v == num {
				exist = true
				break
			}
		}
		if !exist {
			nums = append(nums, num)
		}
	}

	return nums
}

//对密文数组求和
func cipertextArraySum(
	array []*paillier.Ciphertext,
	length int,
	key *paillier.ThresholdPrivateKey,
) (
	encryptedSum *paillier.Ciphertext,
) {
	encryptedSum = key.Encrypt(big.NewInt(0))
	for i := 0; i < length; i++ {
		encryptedSum = key.EAdd(encryptedSum, array[i])
	}
	return encryptedSum
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
