# library/views.py  

from rest_framework import viewsets, status , filters
from rest_framework import filters 
from rest_framework.response import Response 
from rest_framework.permissions import IsAuthenticated 
from django.shortcuts import get_object_or_404  
from django.utils import timezone  
from datetime import timedelta    
from .models import Book, Transaction, CustomUser 
from .serializers import BookSerializer, TransactionSerializer, UserSerializer
from .utils import send_email_notification





class UserViewSet(viewsets.ModelViewSet):  
    """  
    A viewset for viewing and editing user instances.  
    Supports CRUD operations for users.  
    """  
    permission_classes = [IsAuthenticated]
    queryset = CustomUser.objects.all()  
    serializer_class = UserSerializer  


class BookViewSet(viewsets.ModelViewSet):  
    """  
    A viewset for viewing and editing book instances.  
    Supports CRUD operations for books.  
    """  
    permission_classes = [IsAuthenticated]
    queryset = Book.objects.all()  
    serializer_class = BookSerializer 
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]  
    search_fields = ['title', 'author', 'isbn']  
    ordering_fields = ['title', 'author', 'published_date']  

    def create(self, request, *args, **kwargs):  
        """  
        Create a new book instance.  
        """  
        serializer = self.get_serializer(data=request.data)  
        serializer.is_valid(raise_exception=True)  
        self.perform_create(serializer)  
        return Response(serializer.data, status=status.HTTP_201_CREATED)  

class TransactionViewSet(viewsets.ViewSet):  
    """  
    A viewset for managing transactions (checkouts and returns).  
    """  
    permission_classes = [IsAuthenticated]

    def notify_user(self, user, message):  
        subject = 'Library Notification'  
        send_email_notification(user.email, subject, message)  

    def checkout(self, request, pk=None):  
        """  
        Check out a book for the authenticated user.  
        """  
        book = get_object_or_404(Book, pk=pk)  
        if book.copies_available > 0:  
            transaction = Transaction.objects.create(user=request.user, book=book)  
            book.copies_available -= 1  
            book.save()  
            return Response(TransactionSerializer(transaction).data, status=status.HTTP_201_CREATED)  
        return Response({"detail": "No copies available."}, status=status.HTTP_400_BAD_REQUEST)  

    def return_book(self, request, pk=None):  
        """  
        Return a checked-out book for the authenticated user.  
        """  
        transaction = get_object_or_404(Transaction, pk=pk, user=request.user, return_date=None)  
        transaction.return_date = timezone.now()  
        transaction.book.copies_available += 1  
        transaction.book.save()  
        transaction.save()  
        return Response({"detail": "Book returned successfully."}, status=status.HTTP_200_OK)  

    def list(self, request):  
        """  
        List all transactions for the authenticated user.  
        """  
        transactions = Transaction.objects.filter(user=request.user, return_date=None, checkout_date__lt=timezone.now() - timedelta(days=14))  
        serializer = TransactionSerializer(transactions, many=True)  
        return Response(serializer.data)
    


     