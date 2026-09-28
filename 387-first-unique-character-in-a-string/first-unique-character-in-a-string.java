class Solution {
    public int firstUniqChar(String s) {
        Map<Character,Integer> map = new HashMap<>();
        Set<Character> set = new HashSet<>();
        for(int i=0;i<s.length();i++){
            if(map.containsKey(s.charAt(i))){
                map.remove(s.charAt(i));
                set.add(s.charAt(i));
            }
            map.put(s.charAt(i),1);
            if(set.contains(s.charAt(i)))
                map.remove(s.charAt(i));
        }
        for(int i=0;i<s.length();i++){
            if(map.containsKey(s.charAt(i)))
                return i;
        }
        return -1;
    }
}