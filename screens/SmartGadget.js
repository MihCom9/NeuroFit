import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Alert
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

const SmartGadgetScreen = ({ navigation }) => {
  const [exerciseName, setExerciseName] = useState('');
  const [exercises, setExercises] = useState([]);

  useEffect(() => {
    const loadExercises = async () => {
      try {
        const storedExercises = await AsyncStorage.getItem('exercises');
        if (storedExercises) {
          setExercises(JSON.parse(storedExercises));
        }
      } catch (error) {
        console.log('Failed to load exercises:', error);
      }
    };
    loadExercises();
  }, []);

  const saveExercises = async (exercises) => {
    try {
      await AsyncStorage.setItem('exercises', JSON.stringify(exercises));
    } catch (error) {
      console.log('Failed to save exercises:', error);
    }
  };

  const addExercise = () => {
    if (exerciseName.trim()) {
      const newExercises = [...exercises, { id: Date.now().toString(), name: exerciseName }];
      setExercises(newExercises);
      saveExercises(newExercises);
      setExerciseName('');
    }
  };

  const deleteExercise = (id) => {
    const updatedExercises = exercises.filter(exercise => exercise.id !== id);
    setExercises(updatedExercises);
    saveExercises(updatedExercises);
  };

  const handleExercisePress = (exerciseName) => {
    navigation.navigate('ExerciseDetail', { exerciseName });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Exercises</Text>

      
      <TextInput
        style={styles.input}
        value={exerciseName}
        onChangeText={setExerciseName}
        placeholder="Enter exercise name"
        placeholderTextColor="#888"
      />

      <TouchableOpacity style={styles.addButton} onPress={addExercise}>
        <Ionicons name="add-circle-outline" size={24} color="white" />
        <Text style={styles.addButtonText}>Add Exercise</Text>
      </TouchableOpacity>

      
      <FlatList
        data={exercises}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.exerciseContainer}>
            <TouchableOpacity
              style={styles.exercise}
              onPress={() => handleExercisePress(item.name)}
            >
              <Text style={styles.exerciseText}>{item.name}</Text>
            </TouchableOpacity>

            <TouchableOpacity
  style={styles.deleteButton}
  onPress={() =>
    Alert.alert(
      'Delete Exercise',
      'Are you sure you want to delete this exercise?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'OK', onPress: () => deleteExercise(item.id) },
      ],
      { cancelable: true }
    )
  }
>
  <Ionicons name="trash-outline" size={20} color="#fff" />
</TouchableOpacity>

          </View>
        )}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f4f8',
    paddingHorizontal: 20,
    paddingTop: 40,
  },
  header: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
    textAlign: 'center',
  },
  input: {
    height: 45,
    borderColor: '#ccc',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    marginBottom: 15,
    fontSize: 16,
    backgroundColor: '#fff',
    color: '#333',
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007bff',
    paddingVertical: 12,
    borderRadius: 8,
    marginBottom: 20,
  },
  addButtonText: {
    color: '#fff',
    fontSize: 18,
    marginLeft: 10,
    fontWeight: '600',
  },
  exerciseContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
    backgroundColor: '#fff',
    padding: 15,
    borderRadius: 10,
    elevation: 3,
  },
  exercise: {
    flex: 1,
  },
  exerciseText: {
    fontSize: 18,
    color: '#333',
    fontWeight: '600',
  },
  deleteButton: {
    marginLeft: 10,
    backgroundColor: '#ff4d4d',
    padding: 10,
    borderRadius: 30,
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default SmartGadgetScreen;
