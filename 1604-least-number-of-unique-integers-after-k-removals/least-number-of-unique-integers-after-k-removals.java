class Solution {
    public int findLeastNumOfUniqueInts(int[] arr, int k) {
        int n = arr.length;
        HashMap<Integer,Integer> map = new HashMap<>();
        for(int i=0;i<n;i++){
            map.put(arr[i],map.getOrDefault(arr[i],0)+1);
        }
        List<Integer> list = new ArrayList<>();
        for(int i=0;i<n;i++){
            if(map.containsKey(arr[i])){
                list.add(map.get(arr[i]));
                map.remove(arr[i]);
            }
        }
        Collections.sort(list);
        int unique = list.size();
        for(int i=0;i<list.size();i++){
            if(k>=list.get(i)){
                k = k - list.get(i);
                unique -= 1;
            }else{
                return unique;
            }
        }
        return unique;
    }
}