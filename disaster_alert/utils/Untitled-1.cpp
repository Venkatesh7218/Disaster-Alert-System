#include <iostream>
#include <vector>
#include <fstream>
#include <ctime>
using namespace std;

class Transaction {
public:
    string type;
    double amount;
    string time;
};

vector<Transaction> transactions;

string getTime() {
    time_t now = time(0);
    return ctime(&now);
}

void addTransaction() {
    Transaction t;
    cout << "Enter type (deposit/withdraw): ";
    cin >> t.type;
    cout << "Enter amount: ";
    cin >> t.amount;
    t.time = getTime();

    transactions.push_back(t);
    cout << "Transaction added!\n";
}

void showMiniStatement() {
    cout << "\n--- Mini Statement ---\n";

    int start = max(0, (int)transactions.size() - 5);

    ofstream file("statement.txt", ios::app);

    for (int i = start; i < transactions.size(); i++) {
        cout << transactions[i].type << " | "
             << transactions[i].amount << " | "
             << transactions[i].time;

        file << transactions[i].type << " | "
             << transactions[i].amount << " | "
             << transactions[i].time;
    }

    file.close();
}

int main() {
    int choice;

    do {
        cout << "\n1. Add Transaction\n2. Mini Statement\n3. Exit\n";
        cout << "Enter choice: ";
        cin >> choice;

        switch (choice) {
            case 1: addTransaction(); break;
            case 2: showMiniStatement(); break;
            case 3: cout << "Exiting...\n"; break;
            default: cout << "Invalid choice!\n";
        }
    } while (choice != 3);

    return 0;
}