class Solution {
    public String reverseStr(String s, int k) {
        char arr[] = s.toCharArray();
        int i=0;
        int j = Math.min(k - 1, s.length() - 1);
        int changei = 2;
        int changej = 3;
        while(i<s.length()){
            while(i<j){
                char temp = arr[i];
                arr[i] = arr[j];
                arr[j] = temp;
                i++;
                j--;
            }
            i = changei*k;
            j = Math.min(changej*k - 1,s.length()-1);
            changei += 2;
            changej += 2;
        }
        return new String(arr);
    }
}