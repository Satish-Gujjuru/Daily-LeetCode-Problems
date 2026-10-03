class Solution {
    public double myPow(double x, int n) {
        double a = x;
        double ans = 1;
        boolean negative = false;
        if(n<0)
            negative = true;

        if(n < 0){
            long exp = n;
            exp = -exp;
            while(exp>0){
                if(exp%2 != 0)
                    ans = ans*a;
                a = a*a;
                exp = exp>>1;
            }
        }

        while(n>0){
            if(n%2 != 0)
                ans = ans*a;
            a = a*a;
            n = n>>1;
        }
        if(negative)
            return 1/ans;
        return ans;
    }
}