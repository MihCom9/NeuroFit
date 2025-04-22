import React, { useState, useEffect } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  Pressable,
  Platform,
} from 'react-native';
import {
  TextInput,
  Button,
  Checkbox,
  ProgressBar,
  Text,
  Card,
  Divider,
} from 'react-native-paper';
import AsyncStorage from '@react-native-async-storage/async-storage';
import DateTimePickerModal from 'react-native-modal-datetime-picker';

const API_URL = 'http://172.20.10.3:8080/chat';

const HomeScreen = () => {
  const [aiResponse, setAiResponse] = useState('');
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');
  const [weight, setWeight] = useState(3);
  const [hovered, setHovered] = useState(null); // For hover state
  const [deadline, setDeadline] = useState(new Date());
  const [showForm, setShowForm] = useState(false);
  const [isDatePickerVisible, setDatePickerVisibility] = useState(false);
  const [editingTaskId, setEditingTaskId] = useState(null);

  useEffect(() => {
    loadTasks();
  }, []);

  useEffect(() => {
    saveTasks();
  }, [tasks]);

  const addTask = () => {
    if (!title || !weight) return;
    const newTask = {
      id: Date.now(),
      title,
      desc,
      weight,
      deadline: deadline.toDateString(),
      checked: false,
    };
    setTasks([newTask, ...tasks]);
    resetForm();
  };

  const updateTask = () => {
    const updatedTasks = tasks.map((task) =>
      task.id === editingTaskId
        ? { ...task, title, desc, weight, deadline: deadline.toDateString() }
        : task
    );
    setTasks(updatedTasks);
    resetForm();
  };

  const deleteTask = (id) => {
    setTasks(tasks.filter((task) => task.id !== id));
  };

  const resetForm = () => {
    setTitle('');
    setDesc('');
    setWeight(3);
    setDeadline(new Date());
    setEditingTaskId(null);
    setShowForm(false);
  };

  const toggleTask = (id) => {
    setTasks(tasks.map(t => t.id === id ? { ...t, checked: !t.checked } : t));
  };

  const totalWeight = tasks.reduce((sum, t) => sum + t.weight, 0);
  const completedWeight = tasks.filter(t => t.checked).reduce((sum, t) => sum + t.weight, 0);
  const progress = totalWeight > 0 ? completedWeight / totalWeight : 0;

  const saveTasks = async () => {
    try {
      await AsyncStorage.setItem('tasks', JSON.stringify(tasks));
    } catch (err) {
      console.log('Error saving tasks:', err);
    }
  };

  const loadTasks = async () => {
    try {
      const stored = await AsyncStorage.getItem('tasks');
      if (stored) setTasks(JSON.parse(stored));
    } catch (err) {
      console.log('Error loading tasks:', err);
    }
  };

  const handleConfirm = (date) => {
    setDeadline(date);
    setDatePickerVisibility(false);
  };

  const sendToAI = async () => {
    const taskDetails = tasks.map((task) => ({
      title: task.title,
      description: task.desc
    }));

    const formattedTaskDetails = taskDetails
      .map(
        (task, index) =>
          `Task ${index + 1}:\nTitle: ${task.title}\nDescription: ${task.description}\n`
      )
      .join('\n');

    const message = `
      Please help me with the following tasks. Provide clear completion steps for each one, 100 words for a task, no yapping:
  
      ${formattedTaskDetails}
    `;

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });

      const data = await res.json();

      if (data?.reply) {
        setAiResponse(data.reply);
      } else {
        setAiResponse('No response from AI.');
      }
    } catch (e) {
      console.error('AI error:', e);
      setAiResponse('Failed to connect to server. Make sure your IP is correct and server is running.');
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text variant="titleLarge" style={styles.title}>📋 Task Tracker</Text>

      <Text style={styles.progressText}>Progress: {(progress * 100).toFixed(0)}%</Text>
      <ProgressBar progress={progress} style={styles.progress} />

      <Button
        mode="contained"
        onPress={() => setShowForm(!showForm)}
        style={styles.toggleButton}
      >
        {showForm ? 'Cancel' : 'Add New Task'}
      </Button>

      {showForm && (
        <View style={styles.formContainer}>
          <TextInput
            label="Title"
            value={title}
            onChangeText={setTitle}
            mode="outlined"
            style={styles.input}
          />
          <TextInput
            label="Description"
            value={desc}
            onChangeText={setDesc}
            mode="outlined"
            style={styles.input}
            multiline
          />

          <Text variant="labelLarge" style={styles.label}>Weight: {weight}</Text>
          <View style={styles.sliderContainer}>
            {[1, 2, 3, 4, 5].map(num => (
              <Pressable
                key={num}
                onPress={() => setWeight(num)}
                onHoverIn={() => setHovered(num)}
                onHoverOut={() => setHovered(null)}
                style={[
                  styles.weightButton,
                  weight === num && styles.activeWeightButton,
                  hovered === num && styles.hoveredWeightButton
                ]}
              >
                <Text style={styles.weightButtonText}>{num}</Text>
              </Pressable>
            ))}
          </View>

          <Button
            mode="outlined"
            onPress={() => setDatePickerVisibility(true)}
            style={styles.input}
          >
            Pick Deadline: {deadline.toDateString()}
          </Button>

          <DateTimePickerModal
            isVisible={isDatePickerVisible}
            mode="date"
            onConfirm={handleConfirm}
            onCancel={() => setDatePickerVisibility(false)}
            themeVariant="light"
          />

          <Button mode="contained" onPress={editingTaskId ? updateTask : addTask} style={styles.saveButton}>
            {editingTaskId ? 'Update Task' : 'Save Task'}
          </Button>
        </View>
      )}

      <Divider style={{ marginBottom: 10 }} />

      {tasks.map(task => (
        <Card key={task.id} style={styles.card}>
          <Card.Title title={task.title} />
          <Card.Content>
            <Text>Description: {task.desc}</Text>
            <Text>Weight: {task.weight}</Text>
            <Text>Deadline: {task.deadline}</Text>
            <View style={styles.checkboxRow}>
              <Checkbox
                status={task.checked ? 'checked' : 'unchecked'}
                onPress={() => toggleTask(task.id)}
              />
              <Text>{task.checked ? 'Completed' : 'Incomplete'}</Text>
            </View>
          </Card.Content>
          <Card.Actions style={styles.cardActions}>
            <Button
              mode="outlined"
              onPress={() => {
                setTitle(task.title);
                setDesc(task.desc);
                setWeight(task.weight);
                setDeadline(new Date(task.deadline));
                setEditingTaskId(task.id);
                setShowForm(true);
              }}
              style={styles.editButton}
            >
              Edit
            </Button>
            <Button
              mode="outlined"
              onPress={() => deleteTask(task.id)}
              style={styles.deleteButton}
            >
              Delete
            </Button>
          </Card.Actions>
        </Card>
      ))}

      <Button
        mode="contained"
        onPress={sendToAI}
        style={styles.toggleButton}
      >
        Ask AI for help
      </Button>

      {aiResponse ? (
        <View style={styles.responseBox}>
          <Text style={styles.responseTitle}>AI Response:</Text>
          <Text>{aiResponse}</Text>
        </View>
      ) : null}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { padding: 20, marginTop: 40 },
  title: { marginBottom: 20, fontWeight: 'bold', textAlign: 'center' },
  progressText: { marginBottom: 5, fontSize: 16 },
  progress: { height: 10, marginBottom: 15, borderRadius: 10, backgroundColor: '#87cefa' },
  toggleButton: { marginBottom: 15, borderRadius: 10, backgroundColor: '#007bff' },
  formContainer: {
    backgroundColor: '#f4f4f4',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20
  },
  input: {
    marginBottom: 10,
    borderRadius: 10
  },
  saveButton: {
    marginTop: 10,
    borderRadius: 10,
    backgroundColor: '#007bff'
  },
  label: {
    marginVertical: 5
  },
  sliderContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 15
  },
  weightButton: {
    flex: 1,
    marginHorizontal: 4,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: '#eee',
    alignItems: 'center',
    justifyContent: 'center',
    transitionDuration: '150ms',
  },
  hoveredWeightButton: {
    backgroundColor: '#d0e6ff',
  },
  activeWeightButton: {
    backgroundColor: '#007bff',
  },
  weightButtonText: {
    fontWeight: 'bold',
    color: '#000'
  },
  card: {
    marginBottom: 15,
    borderRadius: 10
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
  },
  cardActions: {
    justifyContent: 'space-between',
    paddingHorizontal: 10,
    paddingVertical: 5
  },
  editButton: {
    flex: 1,
    marginRight: 5
  },
  deleteButton: {
    flex: 1,
    marginLeft: 5
  },
  responseBox: {
    marginTop: 20,
    padding: 15,
    borderRadius: 10,
    backgroundColor: '#eef',
  },
  responseTitle: {
    fontWeight: 'bold',
    marginBottom: 5,
  },
});

export default HomeScreen;
