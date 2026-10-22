/**
 * Definition for singly-linked list.
 * public class ListNode {
 *     int val;
 *     ListNode next;
 *     ListNode() {}
 *     ListNode(int val) { this.val = val; }
 *     ListNode(int val, ListNode next) { this.val = val; this.next = next; }
 * }
 */
class Solution {
    public boolean isPalindrome(ListNode head) {
        Stack<Integer> stack = new Stack<>();
        ListNode temp = head;
        int count = 0;
        while (temp != null) {
            count++;
            temp = temp.next;
        }
        ListNode current = head;
        int n = 0;
        for (int i = 0; i < count / 2; i++) {
            stack.push(current.val);
            current = current.next;
        }
        if (count % 2 != 0) {
            current = current.next;
        }
        while (current != null) {
            if (stack.isEmpty()) {
                return false;
            } else {
                if (stack.peek() == current.val) {
                    stack.pop();
                } else {
                    return false;
                }
            }
            current = current.next;
        }
        if (!stack.isEmpty())
            return false;
        return true;
    }
}