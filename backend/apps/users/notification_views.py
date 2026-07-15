from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification

class NotificationListView(APIView):
    """Get all notifications for the current user."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]
        data = [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat()
        } for n in notifications]
        
        unread_count = sum(1 for n in data if not n['is_read'])
        
        return Response({
            'unread_count': unread_count,
            'notifications': data
        })

class NotificationMarkReadView(APIView):
    """Mark a specific notification or all notifications as read."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk=None):
        if pk:
            try:
                notif = Notification.objects.get(id=pk, user=request.user)
                notif.is_read = True
                notif.save()
            except Notification.DoesNotExist:
                return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Mark all as read
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            
        return Response({'status': 'success'})
