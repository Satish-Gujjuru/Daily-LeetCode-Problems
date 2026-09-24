class Solution {
    public boolean isIsomorphic(String s, String t) {
        if(s.length() != t.length())
            return false;

        Map<Character,Character> maps = new HashMap<>();
        Map<Character,Character> mapt = new HashMap<>();

        for(int i=0;i<s.length();i++){
            maps.put(s.charAt(i),t.charAt(i));
            mapt.put(t.charAt(i),s.charAt(i));
        }
        for(int i=0;i<s.length();i++){
            if(t.charAt(i) != maps.get(s.charAt(i)) || s.charAt(i) != mapt.get(t.charAt(i)))
                return false;
        }
        return true;
    }
}