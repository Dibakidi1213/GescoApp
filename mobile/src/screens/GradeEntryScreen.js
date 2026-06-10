import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, Button, FlatList, StyleSheet, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import SQLite from 'react-native-sqlite-storage';

const db = SQLite.openDatabase({ name: 'SchoolOffline.db', location: 'default' });

const GradeEntryScreen = ({ route }) => {
  const { subjectId, classId } = route.params;
  const [students, setStudents] = useState([]);
  const [grades, setGrades] = useState({}); // {studentId: value}
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    setupDatabase();
    loadStudents();
  }, []);

  const setupDatabase = () => {
    db.transaction(tx => {
      tx.executeSql(
        'CREATE TABLE IF NOT EXISTS offline_grades (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INT, subject_id INT, value REAL, period TEXT, sync_status INT DEFAULT 0)'
      );
    });
  };

  const saveGradeLocally = (studentId, value) => {
    db.transaction(tx => {
      tx.executeSql(
        'INSERT INTO offline_grades (student_id, subject_id, value, period) VALUES (?, ?, ?, ?)',
        [studentId, subjectId, value, '1èP'],
        () => Alert.alert("Sauvegardé localement (Hors-ligne)")
      );
    });
  };

  const syncGrades = async () => {
    // Fonction pour synchroniser quand la connexion revient
    db.transaction(tx => {
      tx.executeSql('SELECT * FROM offline_grades WHERE sync_status = 0', [], async (tx, results) => {
        let len = results.rows.length;
        for (let i = 0; i < len; i++) {
          let row = results.rows.item(i);
          try {
            const response = await fetch('https://api.school.com/api/professeur/grades', {
              method: 'POST',
              headers: { 'Authorization': `Bearer ${await AsyncStorage.getItem('access_token')}`, 'Content-Type': 'application/json' },
              body: JSON.stringify(row)
            });
            if (response.ok) {
              tx.executeSql('UPDATE offline_grades SET sync_status = 1 WHERE id = ?', [row.id]);
            }
          } catch (err) {
            console.log("Sync failed, will retry later");
          }
        }
      });
    });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Saisie des notes</Text>
      <FlatList
        data={students}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <Text>{item.name}</Text>
            <TextInput
              style={styles.input}
              keyboardType="numeric"
              onChangeText={(val) => setGrades({...grades, [item.id]: val})}
            />
            <Button title="Sauver" onPress={() => saveGradeLocally(item.id, grades[item.id])} />
          </View>
        )}
        keyExtractor={item => item.id.toString()}
      />
      <Button title="Synchroniser maintenant" onPress={syncGrades} color="#2c3e50" />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20 },
  title: { fontSize: 20, fontWeight: 'bold', marginBottom: 20 },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 },
  input: { borderBottomWidth: 1, width: 50, textAlign: 'center' }
});

export default GradeEntryScreen;
