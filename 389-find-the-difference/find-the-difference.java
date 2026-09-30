class Solution {
    public char findTheDifference(String s, String t) {
        HashMap<Character,Integer> map = new HashMap<>();
        for(int i=0;i<t.length();i++){
            map.put(t.charAt(i),map.getOrDefault(t.charAt(i),0)+1);
        }
        for(int i=0;i<s.length();i++){
            if(map.containsKey(s.charAt(i)))
                map.put(s.charAt(i),map.getOrDefault(s.charAt(i),0)-1);

            if(map.get(s.charAt(i)) == 0)
                map.remove(s.charAt(i));

        }
        char ch = map.keySet().iterator().next();
        return ch;
    }
}